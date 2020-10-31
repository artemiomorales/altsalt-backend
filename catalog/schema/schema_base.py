import graphene
from catalog.models import Culture, Continent
from graphene_django.types import DjangoObjectType
from django.conf import settings
from django.middleware.csrf import _sanitize_token, _compare_salted_tokens
from graphql import GraphQLError

import os
import base64
import PIL.Image as ImageUtils
from django.core.files.uploadhandler import InMemoryUploadedFile
from io import BytesIO
from django.core.files.base import ContentFile

from catalog.backends import CatalogImageStorage
from django.template.defaultfilters import slugify
import logging

class BaseImageTypeMixin:

    def resolve_original(self, info):
        if self.original is not None and self.original.name:
            return self.original.url

        return ''

    def resolve_large(self, info):
        if self.large is not None and self.large.name:
            return self.large.url

        return ''

    def resolve_medium(self, info):
        if self.medium is not None and self.medium.name:
            return self.medium.url

        return ''

    def resolve_small(self, info):
        if self.small is not None and self.small.name:
            return self.small.url

        return ''


def check_csrf(f):

    def wrapper(cls, self, info, **kwargs):
        if settings.CSRF_COOKIE_NAME in info.context.COOKIES and \
                'X-Csrftoken' in info.context.headers:

            csrf_cookie = info.context.COOKIES[settings.CSRF_COOKIE_NAME]
            csrf_token = _sanitize_token(info.context.headers['X-Csrftoken'])

            if _compare_salted_tokens(csrf_cookie, csrf_token):
                return f(cls, self, info, **kwargs)
            else:
                raise GraphQLError("CSRF verification failed.")

        else:
            raise GraphQLError("CSRF verification failed.")

    return wrapper


DEFAULT_IMAGE_SIZES = [
    {'attribute': 'original', 'suffix': ''},
    {'attribute': 'large', 'suffix': '-1x'},
    {'attribute': 'medium', 'suffix': '-1x'},
    {'attribute': 'small', 'suffix': '-1x'},
]


def delete_image_data(image_field):

    storage_delete = CatalogImageStorage()

    for size in DEFAULT_IMAGE_SIZES:
        image_name = getattr(image_field, size['attribute']).name
        storage_delete.delete(image_name)


def save_image_data(image_field, image_data, image_name):
    format, imgstr = image_data.split(';base64,')
    ext = format.split('/')[-1]
    opened_image = ImageUtils.open(BytesIO(base64.b64decode(imgstr + "===")))

    for size in DEFAULT_IMAGE_SIZES:
        buffer = BytesIO()
        copied_image = opened_image.copy()
        copied_image.save(fp=buffer, format=ext, optimize=True)
        temp_file = ContentFile(buffer.getvalue())
        data = InMemoryUploadedFile(temp_file, None, image_name, 'text/plain', len(temp_file), None,
                                    format)
        filename, file_extension = os.path.splitext(image_name)
        getattr(image_field, size['attribute']).save(
            name="{0}-{1}{2}{3}".format(filename, size['attribute'], size['suffix'], file_extension), content=data)


def CreateCulture(culture_name, culture_slug, continent_name=None):

    new_culture = Culture(name=culture_name.title(), slug=culture_slug)
    if continent_name is not None:
        continent_slug = slugify(continent_name)
        continent = Continent.objects.get(slug=continent_slug)
        new_culture.continent = continent

    new_culture.save()

    return new_culture


class CultureType(DjangoObjectType):
    class Meta:
        model = Culture


class NameWithPriorityInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    priority = graphene.Int(required=True)


class LinkInput(NameWithPriorityInput):
    url = graphene.String(required=True)


class CultureInput(NameWithPriorityInput):
    continent = graphene.String()