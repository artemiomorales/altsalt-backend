import os
from os.path import join, dirname
from dotenv import load_dotenv
from django.utils.deprecation import MiddlewareMixin

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

debug = True if os.environ.get('DEBUG') == 'True' else False


class IntrospectionDisabledException(Exception):
    pass


class DisableIntrospectionMiddleware(object):
    def resolve(self, next, root, info, **kwargs):
        if debug is False and info.field_name.lower() in ['__schema', '__introspection']:
            raise IntrospectionDisabledException
        return next(root, info, **kwargs)


class CacheMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        response['Cache-Control'] = 'max-age=0, no-cache, no-store, must-revalidate, private'
        return response
