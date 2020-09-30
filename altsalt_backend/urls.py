"""altsalt_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from graphql_jwt.decorators import jwt_cookie
from catalog import views

import os
from os.path import join, dirname
from dotenv import load_dotenv

# Graphene
from graphene_django.views import GraphQLView


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

require_csrf = False if \
    os.environ.get('REQUIRE_CSRF') == 'False' else True

graphql_view = jwt_cookie(GraphQLView.as_view(graphiql=True)) if require_csrf is True\
        else jwt_cookie(csrf_exempt(GraphQLView.as_view(graphiql=True)))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', graphql_view),
    # path('graphql/', jwt_cookie(csrf_exempt(GraphQLView.as_view(graphiql=True)))),
    # path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('csrf/', csrf_exempt(views.csrf)),
    path('ping/', views.ping),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
