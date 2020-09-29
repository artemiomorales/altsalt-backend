from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse
from django.middleware.csrf import get_token


def csrf(request):
    csrf_data = get_token(request)
    response = JsonResponse({'csrfToken': csrf_data})
    # JsonResponse({'csrfToken': get_token(request)})
    response.set_cookie('csrftoken', csrf_data, max_age=None, expires=None, path='/',
                        domain='altsalt-local.com', secure=True, httponly=False, samesite=None)
    response.cookies['csrftoken']['samesite'] = 'None'
    return response


def ping(request):
    return JsonResponse({'result': 'OK'})