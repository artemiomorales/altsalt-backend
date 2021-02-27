from django.apps import AppConfig
from django.db.models.signals import post_save, pre_delete
import logging


class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):

        from catalog.signals import on_image_delete
        from catalog.signals import on_file_delete
        from catalog.signals import on_submission_delete
        from catalog.signals import on_comment_delete
        from catalog.signals import on_comment_reaction_delete
        from catalog.signals import on_listing_thread_delete
