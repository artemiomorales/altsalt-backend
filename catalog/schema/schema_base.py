from catalog.models import Culture
from graphene_django.types import DjangoObjectType
from django.conf import settings
from django.middleware.csrf import _sanitize_token, _compare_salted_tokens
from graphql import GraphQLError

import logging


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


class CultureType(DjangoObjectType):
    class Meta:
        model = Culture
