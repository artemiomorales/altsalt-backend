from graphql_jwt.backends import JSONWebTokenBackend
from graphql_jwt.shortcuts import get_user_by_token
from graphql_jwt.utils import get_credentials
from graphql_jwt.exceptions import JSONWebTokenError

import os
from os.path import join, dirname
from storages.backends.s3boto3 import S3Boto3Storage
from dotenv import load_dotenv

import base64
from django.core.files.base import ContentFile
import PIL.Image as ImageUtils
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

import io
from io import BytesIO

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

import logging


class GraphQLAuthBackend(JSONWebTokenBackend):
    """
    Only difference from the original backend
    is it does not raise when fail on get_user_by_token
    preventing of raise when client send token to a
    mutation that does not requery login but is not on
    allow any settings.
    Main advantage is to let the mutation handle the
    unauthentication error. Intead of an actual error,
    we can return e.g. success=False errors=Unauthenticated
    """

    def authenticate(self, request=None, **kwargs):
        if request is None or getattr(request, "_jwt_token_auth", False):
            return None

        token = get_credentials(request, **kwargs)

        try:  # +++
            if token is not None:
                return get_user_by_token(token, request)
        except JSONWebTokenError:  # +++
            pass  # +++

        return None


class ProfileImageStorage(S3Boto3Storage):
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    target_width = None
    target_height = None
    name_suffix = None
    save_thumbnails = False

    def __init__(self, target_width, target_height, name_suffix, save_thumbnails=False):
        super().__init__()

        self.target_width = target_width
        self.target_height = target_height
        self.name_suffix = name_suffix
        self.save_thumbnails = save_thumbnails

    def _save(self, name, content):

        logging.error(content.__dict__.keys())
        logging.error(type(content))

        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        params = self._get_write_parameters(name, content)

        filename, file_extension = os.path.splitext(name)

        if content.content_type_extra is not None and isinstance(content.content_type_extra, str):
            content_type = content.content_type_extra.split('/')[-1]
        else:
            content_type = content.content_type.split('/')[-1]

        logging.error(content_type)


        # Open image
        initial_buffer = io.BufferedRandom(io.BytesIO())
        if content.multiple_chunks():
            for chunk in content.chunks():
                initial_buffer.write(chunk)
        else:
            initial_buffer = BytesIO(content.read())
        opened_image = ImageUtils.open(initial_buffer)


        if self.save_thumbnails is False:

            og_buffer = BytesIO()
            og_image = opened_image.copy()
            og_image.thumbnail((self.target_width, self.target_height))
            og_image.save(fp=og_buffer, format=content_type, optimize=True)
            og_data = ContentFile(og_buffer.getvalue())

            if (self.gzip and
                    params['ContentType'] in self.gzip_content_types and
                    'ContentEncoding' not in params):
                og_data = self._compress_content(content)
                params['ContentEncoding'] = 'gzip'

            # Save the original image
            encoded_name = self._encode_name('{0}-{1}{2}'.format(filename, self.name_suffix, file_extension))
            og_obj = self.bucket.Object(encoded_name)

            if self.preload_metadata:
                self._entries[encoded_name] = og_obj

            og_data.seek(0, os.SEEK_SET)
            og_obj.upload_fileobj(og_data, ExtraArgs=params)

        else:

            responsive_sizes = [1, 2, 3, 4]
            for responsive_size in responsive_sizes:

                # Identify the multiplier
                encoded_name = self._encode_name("{0}-{1}-x{2}{3}".format(filename, self.name_suffix, responsive_size, file_extension))
                tb_obj = self.bucket.Object(encoded_name)
                if self.preload_metadata:
                    self._entries[encoded_name] = tb_obj

                tb_buffer = BytesIO()
                tb_image = opened_image.copy()
                tb_image.thumbnail((self.target_width * responsive_size, self.target_height * responsive_size))
                tb_image.save(fp=tb_buffer, format=content_type, optimize=True)
                tb_data = ContentFile(tb_buffer.getvalue())

                if (self.gzip and
                        params['ContentType'] in self.gzip_content_types and
                        'ContentEncoding' not in params):
                    tb_data = self._compress_content(tb_data)
                    params['ContentEncoding'] = 'gzip'

                # Compress and save resized tb
                tb_data.seek(0, os.SEEK_SET)
                tb_obj.upload_fileobj(tb_data, ExtraArgs=params)

        return cleaned_name

    def delete(self, name):
        name = self._normalize_name(self._clean_name(name))
        self.bucket.Object(self._encode_name(name)).delete()

        filename, file_extension = os.path.splitext(name)

        responsive_sizes = [1, 2, 3, 4]
        for responsive_size in responsive_sizes:
            thumbnail_name = "{0}-x{1}{2}".format(filename, responsive_size, file_extension)
            sanitized_name = self._normalize_name(self._clean_name(thumbnail_name))
            if self.exists(sanitized_name):
                self.bucket.Object(self._encode_name(sanitized_name)).delete()

        if name in self._entries:
            del self._entries[name]

