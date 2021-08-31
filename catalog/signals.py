from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver
from catalog.models import ListingCoverImage, ListingPreviewImage, ListingUpload,\
    Submission, Thread, Comment, CommentReaction, Notification, Article, Listing, PageSectionEntry
from catalog.models.base import ContentThread
from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, DEFAULT_THUMBNAIL_SIZES, RESPONSIVE_SIZES, DEFAULT_FILE_UPLOAD_NAME
from catalog.backends import CatalogImageStorage
from django.contrib.contenttypes.models import ContentType


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


@receiver(pre_delete, sender=ListingUpload)
@receiver(pre_delete, sender=Submission)
def on_file_delete(sender, **kwargs):

    instance = kwargs.get('instance')

    storage = CatalogImageStorage()

    default_attribute = getattr(instance, DEFAULT_FILE_UPLOAD_NAME)
    default_name = default_attribute.name

    if default_name is not None and default_name != '':
        storage.delete(default_name)


@receiver(post_delete, sender=Submission)
def on_submission_delete(sender, **kwargs):
    try:
        instance = kwargs.get('instance')
        if getattr(instance, 'listing') is not None:
            kwargs['instance'].listing.delete()
    except:
        pass


@receiver(post_delete, sender=Comment)
def on_comment_delete(sender, **kwargs):
    try:
        instance = kwargs.get('instance')
        if instance.is_root is True and Thread.objects.filter(id=instance.thread.id).exists():
            thread = Thread.objects.get(id=instance.thread.id)
            thread.delete()

        content_type = ContentType.objects.get_for_model(instance)
        if Notification.objects.filter(content_type=content_type, object_id=instance.id).exists():
            notification = Notification.objects.get(content_type=content_type, object_id=instance.id)
            notification.delete()
    except:
        pass


@receiver(post_delete, sender=CommentReaction)
def on_comment_reaction_delete(sender, **kwargs):
    try:
        instance = kwargs.get('instance')
        content_type = ContentType.objects.get_for_model(instance)

        if Notification.objects.filter(content_type=content_type, object_id=instance.id).exists():
            notification = Notification.objects.get(content_type=content_type, object_id=instance.id)
            notification.delete()

    except:
        pass


@receiver(post_delete, sender=ContentThread)
def on_content_thread_delete(sender, **kwargs):
    try:
        instance = kwargs.get('instance')
        content_type = ContentType.objects.get_for_model(instance)

        if hasattr(instance, 'thread'):
            kwargs['instance'].thread.delete()

        if Notification.objects.filter(content_type=content_type, object_id=instance.id).exists():
            notification = Notification.objects.get(content_type=content_type, object_id=instance.id)
            notification.delete()

    except:
        pass


@receiver(post_delete, sender=Article)
@receiver(post_delete, sender=Listing)
def on_user_content_delete(sender, **kwargs):
    try:
        instance = kwargs.get('instance')
        content_type = ContentType.objects.get_for_model(instance)

        if ContentThread.objects.filter(content_type=content_type, object_id=instance.id).exists():
            content_thread = ContentThread.objects.get(content_type=content_type, object_id=instance.id)
            content_thread.delete()

        if PageSectionEntry.objects.filter(content_type=content_type, object_id=instance.id).exists():
            page_section_entry = PageSectionEntry.objects.get(content_type=content_type, object_id=instance.id)
            page_section_entry.delete()

    except:
        pass