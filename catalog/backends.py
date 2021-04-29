from graphql_jwt.backends import JSONWebTokenBackend
from graphql_jwt.shortcuts import get_user_by_token
from graphql_jwt.utils import get_credentials
from graphql_jwt.exceptions import JSONWebTokenError

from os.path import join, dirname
from dotenv import load_dotenv

import os
from storages.backends.s3boto3 import S3Boto3Storage
import PIL.Image as ImageUtils
from PIL import ImageFile

import io
from io import BytesIO
from catalog.constants import get_image_buffer

ImageFile.LOAD_TRUNCATED_IMAGES = True
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


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


class CatalogImageStorage(S3Boto3Storage):
    bucket_name = os.environ.get('AWS_STORAGE_BUCKET_NAME')


class ThumbnailImageStorage(CatalogImageStorage):
    target_width = None
    target_height = None

    def __init__(self, **kwargs):
        super().__init__()

        self.target_width = kwargs.get('target_width')
        self.target_height = kwargs.get('target_height')

    def _save(self, name, content):

        cleaned_name = self._clean_name(name)
        name = self._normalize_name(cleaned_name)
        params = self._get_write_parameters(name, content)

        # NOTE REGARDING GRAPHQL UPLOADS
        #
        # In order to parse image responses from GraphQL, we need to read in the data as 'text/plain'
        # in the 'content_type' attribute; but we still need to know the image format in order to save
        # properly. So we store the image format inside of 'content_type_extra' and read it from that
        # attribute with this if / else statement.
        #
        import logging
        logging.error(content)
        if content.content_type_extra is not None and isinstance(content.content_type_extra, str):
            mime_type = content.content_type_extra.split('/')[-1]
            params['ContentType'] = 'image/{0}'.format(content.content_type_extra)
        else:
            mime_type = content.content_type.split('/')[-1]
            params['ContentType'] = 'image/{0}'.format(content.content_type)

        # Open image
        initial_buffer = io.BufferedRandom(io.BytesIO())
        if content.multiple_chunks():
            for chunk in content.chunks():
                initial_buffer.write(chunk)
        else:
            initial_buffer = BytesIO(content.read())

        opened_image = ImageUtils.open(initial_buffer)
        opened_image.thumbnail((1588, 2382))
        image_buffer = get_image_buffer(opened_image, mime_type)

        if (self.gzip and
                params['ContentType'] in self.gzip_content_types and
                'ContentEncoding' not in params):
            image_buffer = self._compress_content(content)
            params['ContentEncoding'] = 'gzip'

        # Save the image
        encoded_name = self._encode_name(name)
        og_obj = self.bucket.Object(encoded_name)

        if self.preload_metadata:
            self._entries[encoded_name] = og_obj

        image_buffer.seek(0, os.SEEK_SET)

        og_obj.upload_fileobj(image_buffer, ExtraArgs=params)

        return cleaned_name