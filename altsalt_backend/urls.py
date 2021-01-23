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

# Graphene
from graphene_django.views import GraphQLView
from graphene_protector.django import ProtectorBackend

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

debug = True if os.environ.get('DEBUG') == 'True' else False

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', jwt_cookie(csrf_exempt(GraphQLView.as_view(graphiql=debug, backend=ProtectorBackend())))),
    path('csrf/', csrf_exempt(views.csrf)),
    path('ping/', views.ping),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
