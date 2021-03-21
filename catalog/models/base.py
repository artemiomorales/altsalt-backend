import os
import datetime
import logging

from django.db import models
from django.conf import settings
from django.template.defaultfilters import slugify
from catalog.constants import RESPONSIVE_SIZES
from catalog.backends import CatalogImageStorage
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Image Handling
from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, DEFAULT_THUMBNAIL_SIZES
from catalog.tasks import generate_thumbnails
import threading
from django.db.models import DEFERRED
import PIL.Image as ImageUtils

PROJECT_PREFIX = settings.PROJECT_PREFIX
TABLE_PREFIX = 'catalog_'


class Link(models.Model):
    name = models.CharField(max_length=55)
    url = models.URLField()
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['-priority']


class NameSlug(models.Model):
    name = models.CharField(max_length=55, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.name)

        super(NameSlug, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']


class Continent(NameSlug):

    class Meta:
        db_table = TABLE_PREFIX + 'continent'


class Country(NameSlug):
    continent = models.ForeignKey(Continent, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'country'
        verbose_name_plural = 'Countries'
        ordering = ['name']


class Identity(NameSlug):

    class Meta:
        db_table = TABLE_PREFIX + 'identity'
        verbose_name_plural = 'Identities'
        ordering = ['name']


class CustomSaveMixin(models.Model):
    _loaded_values = None

    @classmethod
    def from_db(cls, db, field_names, values):
        if len(values) != len(cls._meta.concrete_fields):
            values_iter = iter(values)
            values = [
                next(values_iter) if f.attname in field_names else DEFERRED
                for f in cls._meta.concrete_fields
            ]
        new = cls(*values)
        new._state.adding = False
        new._state.db = db
        # customization to store the original field values on the instance
        new._loaded_values = dict(zip(field_names, values))
        return new

    class Meta:
        abstract = True


class CustomImage(CustomSaveMixin):
    loop_executed = False

    def save(self, skip_callback=False, *args, **kwargs):

        super().save(*args, **kwargs)

        if not self._state.adding and skip_callback is False and self.loop_executed is False:

            self.loop_executed = True

            storage = CatalogImageStorage()

            if self._loaded_values is None or DEFAULT_IMAGE_SIZE_NAME not in self._loaded_values or \
                    getattr(self, DEFAULT_IMAGE_SIZE_NAME) != self._loaded_values[DEFAULT_IMAGE_SIZE_NAME]:

                # Delete old images
                if self._loaded_values is not None and DEFAULT_IMAGE_SIZE_NAME in self._loaded_values:
                    old_default_image_name = self._loaded_values[DEFAULT_IMAGE_SIZE_NAME]
                    if old_default_image_name is not None and old_default_image_name != '':
                        storage.delete(old_default_image_name)

                for size in DEFAULT_THUMBNAIL_SIZES:
                    # Delete the old thumbnails
                    if self._loaded_values is not None and size['attribute'] in self._loaded_values:
                        old_thumbnail_name = self._loaded_values[size['attribute']]
                        if old_thumbnail_name is not None and old_thumbnail_name != '':
                            storage.delete(old_thumbnail_name)
                            for responsive_size in RESPONSIVE_SIZES:
                                old_responsive_name = old_thumbnail_name.replace('-1x', "-{0}x".format(responsive_size))
                                storage.delete(old_responsive_name)

                # GENERATING THUMBNAILS IS CURRENTLY DISABLED - THIS IS HANDLED BY THE FRONT END
                #
                # Get a reference to the new image to generate thumbnails
                # new_default_image_attribute = getattr(self, DEFAULT_IMAGE_SIZE_NAME)
                #
                # default_image_data = ImageUtils.open(new_default_image_attribute)
                # mime_type = default_image_data.format
                # directory, filepath = os.path.split(new_default_image_attribute.name)
                # filename, extension = os.path.splitext(filepath)
                # original_filename = filename.split('-original')[0]
                #
                # # Create new thumbnails
                # # Set up another thread to take care of generating thumbnails
                # if skip_callback is False:
                #     thread_args = [
                #         type(self).__name__,
                #         self.id,
                #         mime_type,
                #         original_filename,
                #         ".{0}".format(extension)
                #     ]
                #     generate_thumbnails_thread = threading.Thread(target=generate_thumbnails, args=thread_args)
                #     generate_thumbnails_thread.start()

    class Meta:
        abstract = True


class CustomImageAlttext(CustomImage):
    alttext = models.CharField(max_length=300, default="")

    class Meta:
        abstract = True


class Thread(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    originator = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)

    def get_root_comment(self):

        if Comment.objects.filter(thread=self, is_root=True).exists():
            return Comment.objects.get(thread=self, is_root=True)

        return None

    def __str__(self):
        username = ''
        if self.originator is not None:
            username = self.originator.username

        from catalog.models.listing import ListingThread

        if ListingThread.objects.filter(thread=self).exists():
            listing_thread = ListingThread.objects.get(thread=self)
            return "{0} - {1}".format(listing_thread.listing.title, username)

        return self.id

    class Meta:
        db_table = TABLE_PREFIX + 'thread'
        ordering = ['timestamp']


class Comment(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    commenter = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    body = models.TextField(default="", blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_root = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = TABLE_PREFIX + 'comment'
        ordering = ['timestamp']


class ReactionType(NameSlug):

    class Meta:
        db_table = TABLE_PREFIX + 'reaction_type'


class CommentReaction(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reactor = models.ForeignKey('User', on_delete=models.CASCADE)
    reaction_type = models.ForeignKey(ReactionType, on_delete=models.PROTECT)

    class Meta:
        db_table = TABLE_PREFIX + 'comment_reaction'
        constraints = [
            models.UniqueConstraint(fields=['comment', 'reactor'], name='comment_reactor_link')
        ]


class Notification(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    notifier = models.ForeignKey('User', on_delete=models.CASCADE, related_name="notifier")
    recipient = models.ForeignKey('User', on_delete=models.CASCADE, related_name="recipient")
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def get_type(self):
        from catalog.models.listing import ListingThread
        notification = Notification.objects.get(id=self.id)
        model = notification.content_type.model_class()

        if model is ListingThread:
            return 'comment'

        if model is Comment:
            return 'reply'

        if model is CommentReaction:
            return 'reaction'

        return None

    def get_simple_message(self):
        from catalog.models.listing import ListingThread
        model = self.content_type.model_class()

        if model is ListingThread:
            return '{0} resonated on your listing {1}'.format(self.notifier.display_name,
                                                                     self.content_object.listing.title)
        if model is Comment:
            listing_title = ''
            if ListingThread.objects.filter(thread=self.content_object.thread).exists():
                listing_thread = ListingThread.objects.get(thread=self.content_object.thread)
                listing_title = listing_thread.listing.title
            return '{0} replied on a thread you\'re a part of on {1}'.format(self.notifier.display_name,
                                                                             listing_title)
        if model is CommentReaction:
            listing_title = ''
            if ListingThread.objects.filter(thread=self.content_object.comment.thread).exists():
                listing_thread = ListingThread.objects.get(thread=self.content_object.comment.thread)
                listing_title = listing_thread.listing.title
            return '{0} reacted to your resonance on {1}'.format(self.notifier.display_name,
                                                                listing_title)

        return None

    def get_message(self):
        from catalog.models.listing import ListingThread
        model = self.content_type.model_class()

        def get_thread_string(thread):
            if thread.get_root_comment() is not None:
                return thread.get_root_comment().body

            return ''

        if model is ListingThread:
            return '{0} resonated on your listing {1}: “{2}”'.format(self.notifier.display_name,
                                                                     self.content_object.listing.title,
                                                                     get_thread_string(
                                                                         self.content_object.thread))
        if model is Comment:
            return '{0} replied on a thread you\'re a part of: "{1}”'.format(self.notifier.display_name,
                                                                             get_thread_string(
                                                                                 self.content_object.thread))
        if model is CommentReaction:
            return '{0} reacted 🙏 to your resonance "{1}"'.format(self.notifier.display_name,
                                                                self.content_object.comment.body)

        return None

    def get_url_components(self):
        from catalog.models.listing import ListingThread
        notification = Notification.objects.get(id=self.id)
        model = notification.content_type.model_class()

        if model is ListingThread:
            return {'listing': notification.content_object.listing,
                    'thread': notification.content_object.thread,
                    'comment': None
                    }
        if model is Comment and \
                ListingThread.objects.filter(thread=notification.content_object.thread).exists():
            listing_thread = ListingThread.objects.get(thread=notification.content_object.thread)
            return {'listing': listing_thread.listing,
                    'thread': notification.content_object.thread,
                    'comment': notification.content_object
                    }
        if model is CommentReaction and \
                ListingThread.objects.filter(thread=notification.content_object.comment.thread).exists():
            listing_thread = ListingThread.objects.get(thread=notification.content_object.comment.thread)
            return {'listing': listing_thread.listing,
                    'thread': notification.content_object.comment.thread,
                    'comment': notification.content_object.comment
                    }
        return None

    def __str__(self):
        return "{0} - {1} from {2} - {3}".format(self.recipient.username, self.content_type.name, self.notifier.username, self.id)

    class Meta:
        ordering = ['-timestamp']


def catalog_media_path(media_type, instance_id):
    return 'catalog/{0}/{1}'.format(media_type, instance_id)


def sanitize_filename(filename):
    # Replace any responsive string inside the filename
    # that would interfere with our image handling logic

    sanitized_filename = filename

    image_sizes = RESPONSIVE_SIZES
    image_sizes.append('1x')
    for responsize_size in image_sizes:
        responsive_string = "{0}x".format(responsize_size)
        if responsive_string in sanitized_filename:
            sanitized_filename = sanitized_filename.replace(responsive_string, "00")

    return sanitized_filename

def profile_image_path(instance, filename):
    date = datetime.datetime.now()
    filename, file_extension = os.path.splitext(filename)

    sanitized_filename = sanitize_filename(filename)
    profile_path = catalog_media_path('user', instance.user.id)
    timestamp_id = date.strftime("%f")

    save_string = "{0}/profile-image/{1}-{2}{3}".format(profile_path,
                                                        sanitized_filename, timestamp_id, file_extension)

    return save_string


def content_path(content_type, content_id, media_label, media_id, filename):
    date = datetime.datetime.now()
    filename, file_extension = os.path.splitext(filename)

    sanitized_filename = sanitize_filename(filename)

    listing_path = catalog_media_path(content_type, content_id)
    timestamp_id = date.strftime("%f")
    save_string = "{0}/{1}-{2}/{3}-{4}{5}".format(listing_path, media_label, media_id,
                                                  sanitized_filename, timestamp_id, file_extension)
    return save_string


def listing_cover_image_path(instance, filename):
    return content_path('listing', instance.listing.id, 'cover', instance.id, filename)


def listing_preview_image_path(instance, filename):
    return content_path('listing', instance.listing.id, 'preview', instance.id, filename)


def listing_upload_path(instance, filename):
    listing_path = catalog_media_path('listing', instance.listing.id)
    return "{0}/upload-{1}/{2}".format(listing_path, instance.id, filename)


def submission_upload_path(instance, filename):
    listing_path = catalog_media_path('listing', instance.listing.id)
    return "{0}/submission-{1}/{2}".format(listing_path, instance.id, filename)


def article_cover_image_path(instance, filename):
    return content_path('article', instance.article.id, 'cover', instance.article.id, filename)


def media_upload_path(instance, filename):
    date = datetime.datetime.now()
    return (catalog_media_path(instance.user_id) + "/uploads/{0}-{1}").format(date.strftime("%f"), filename)