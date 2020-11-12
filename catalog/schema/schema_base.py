import graphene
from catalog.models.base import Culture, Continent
from graphene_django.types import DjangoObjectType
from django.conf import settings
from django.middleware.csrf import _sanitize_token, _compare_salted_tokens
from graphql import GraphQLError

import os
import base64
import PIL.Image as ImageUtils
from django.core.files.uploadhandler import InMemoryUploadedFile
from io import BytesIO


from catalog.backends import CatalogImageStorage
from django.template.defaultfilters import slugify
from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, DEFAULT_THUMBNAIL_SIZES, get_image_buffer


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


def save_image_data(model_instance, image_data, image_name):
    prefix, imgstr = image_data.split(';base64,')
    mime_type = prefix.split('/')[-1]

    if 'jpeg' not in mime_type is False and 'png' not in mime_type:
        raise TypeError('Images must be in JPEG or PNG format')

    filename, extension = os.path.splitext(image_name)

    opened_image = ImageUtils.open(BytesIO(base64.b64decode(imgstr + "===")))

    # Save an original image
    image_buffer = get_image_buffer(opened_image, mime_type)
    upload_data = InMemoryUploadedFile(image_buffer, None, image_name, 'text/plain', len(image_buffer), None,
                                       mime_type)
    getattr(model_instance, DEFAULT_IMAGE_SIZE_NAME).save(
        name="{0}-{1}{2}".format(filename, DEFAULT_IMAGE_SIZE_NAME, extension),
        content=upload_data,
        save=False)
    model_instance.save(skip_callback=False)


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