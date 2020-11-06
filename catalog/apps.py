from django.apps import AppConfig
from django.db.models.signals import post_save, pre_delete
import logging

class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):

        from catalog.signals import on_image_delete
