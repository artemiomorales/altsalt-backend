from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from django.middleware.csrf import get_token

import os
from os.path import join, dirname
from dotenv import load_dotenv


def csrf(request):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    secure_csrf = False if \
        os.environ.get('CSRF_COOKIE_SECURE') == 'False' else True

    csrf_data = get_token(request)
    response = JsonResponse({'result': 'OK'})
    response.set_cookie('csrftoken', csrf_data, max_age=None, expires=None, path='/',
                        domain='altsalt-local.com', secure=secure_csrf, httponly=False, samesite=None)
    # response.cookies['csrftoken']['samesite'] = 'None'
    return response


def ping(request):
    return JsonResponse({'result': 'OK'})