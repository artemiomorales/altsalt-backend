from django.db.models.signals import pre_delete
from django.dispatch import receiver
from catalog.models import ListingCoverImage, ListingPreviewImage
from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, DEFAULT_THUMBNAIL_SIZES, RESPONSIVE_SIZES
from catalog.backends import CatalogImageStorage


@receiver(pre_delete, sender=ListingCoverImage)
@receiver(pre_delete, sender=ListingPreviewImage)
def on_image_delete(sender, **kwargs):

    instance = kwargs.get('instance')

    storage = CatalogImageStorage()

    default_image_attribute = getattr(instance, DEFAULT_IMAGE_SIZE_NAME)
    default_image_name = default_image_attribute.name

    if default_image_name is not None and default_image_name != '':
        storage.delete(default_image_name)

    for thumbnail_size in DEFAULT_THUMBNAIL_SIZES:
        thumbnail_name = getattr(instance, thumbnail_size['attribute']).name

        if thumbnail_name is not None and thumbnail_name != '':
            storage.delete(thumbnail_name)

            for responsive_size in RESPONSIVE_SIZES:
                responsive_name = thumbnail_name.replace('-1x', "-{0}x".format(responsive_size))
                storage.delete(responsive_name)