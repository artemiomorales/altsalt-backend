import os
from .base import PROJECT_PREFIX, TABLE_PREFIX, listing_cover_image_path, listing_preview_image_path, Link, NameSlug, Culture
from .user import *
from .image import Image

from django.db import models
from django.template.defaultfilters import slugify
from catalog.backends import CatalogImageStorage, ThumbnailImageStorage
from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, DEFAULT_THUMBNAIL_SIZES, RESPONSIVE_SIZES
from django.db.models import DEFERRED
import PIL.Image as ImageUtils

import logging
import threading
from catalog.tasks import generate_thumbnails

class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField(default="The author(s) haven't provided a description yet.", null=True)
    price = models.ForeignKey("Price", null=True, on_delete=models.SET_NULL)
    format = models.ManyToManyField(
        "Format",
        through='ListingFormat'
    )
    distribution_type = models.ManyToManyField(
        "DistributionType",
        through='ListingDistributionType'
    )
    length = models.ForeignKey("Length", null=True, on_delete=models.PROTECT)
    genre = models.ManyToManyField(
        "Genre",
        through='ListingGenre'
    )
    language = models.ManyToManyField(
        "Language",
        through='ListingLanguage'
    )
    publication_date = models.DateField(null=True)
    date_added = models.DateField()
    is_approved = models.BooleanField(null=True, default=False)
    date_approved = models.DateField(null=True)
    is_published = models.BooleanField(null=True, default=False)
    culture_represented = models.ManyToManyField(
        "Culture",
        through='ListingCultureRepresented'
    )
    content_rating = models.ForeignKey("ContentRating", null=True, on_delete=models.PROTECT)
    seo_category = models.ForeignKey("SeoCategory", null=True, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.title)

        super(Listing, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'listing'


class ListingLink(Link):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)

    class Meta(Link.Meta):
        abstract = True


class ListingAvailabilityLink(ListingLink):

    class Meta(ListingLink.Meta):
        db_table = TABLE_PREFIX + 'listing_availability_link'


class ListingAdditionalLink(ListingLink):

    class Meta(ListingLink.Meta):
        db_table = TABLE_PREFIX + 'listing_additional_link'


class ListingCreatorByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    listing_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_creator_byline'
        constraints = [
            models.UniqueConstraint(fields=['user', 'listing'], name='user_listing_creator_link')
        ]


class ListingCollaboratorByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    listing_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_collaborator_byline'
        constraints = [
            models.UniqueConstraint(fields=['user', 'listing'], name='user_listing_collaborator_link')
        ]


class Format(NameSlug):
    class Meta:
        db_table = TABLE_PREFIX + 'format'


class ListingFormat(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="listing")
    format = models.ForeignKey(Format, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_format'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['listing', 'format'], name='listing_format_link')
        ]


class DistributionType(NameSlug):
    class Meta:
        db_table = TABLE_PREFIX + 'distribution_type'


class ListingDistributionType(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    distribution_type = models.ForeignKey(DistributionType, on_delete=models.CASCADE)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_distribution_type'
        constraints = [
            models.UniqueConstraint(fields=['listing', 'distribution_type'], name='listing_distribution_type_link')
        ]


class Length(NameSlug):
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'length'
        ordering = ['-priority']


class Genre(NameSlug):
    class Meta:
        db_table = TABLE_PREFIX + 'genre'


class ListingGenre(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_genre'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['listing', 'genre'], name='listing_genre_link')
        ]


class Language(NameSlug):
    class Meta:
        db_table = TABLE_PREFIX + 'language'


class ListingLanguage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_language'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['listing', 'language'], name='listing_language_link')
        ]


class ListingCultureRepresented(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_culture_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['listing', 'culture'], name='listing_culture_link')
        ]


class PriceType(NameSlug):
    class Meta:
        db_table = TABLE_PREFIX + 'price_type'


class Price(models.Model):
    price_type = models.ForeignKey(PriceType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    details = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.price_type.name + ' ' + self.amount.__str__()

    class Meta:
        db_table = TABLE_PREFIX + 'price'


class SeoCategory(models.Model):
    name = models.CharField(max_length=55, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = TABLE_PREFIX + 'seo_category'


class ContentRating(NameSlug):
    class Meta:
        db_table = TABLE_PREFIX + 'content_rating'


class ListingImage(models.Model):
    image = models.ForeignKey(Image, null=True, on_delete=models.CASCADE)
    alttext = models.CharField(max_length=300, default="Image alttext")
    _loaded_values = None
    loop_executed = False

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

                # Get a reference to the new image to generate thumbnails
                new_default_image_attribute = getattr(self, DEFAULT_IMAGE_SIZE_NAME)

                default_image_data = ImageUtils.open(new_default_image_attribute)
                mime_type = default_image_data.format
                directory, filepath = os.path.split(new_default_image_attribute.name)
                filename, extension = filepath.split('.')
                original_filename = filename.split('-original')[0]

                # Create new thumbnails
                # Set up another thread to take care of generating thumbnails
                if skip_callback is False:
                    thread_args = [
                        type(self).__name__,
                        self.id,
                        mime_type,
                        original_filename,
                        ".{0}".format(extension)
                    ]
                    generate_thumbnails_thread = threading.Thread(target=generate_thumbnails, args=thread_args)
                    generate_thumbnails_thread.start()

    class Meta:
        abstract = True


class ListingCoverImage(ListingImage):
    id = models.AutoField(primary_key=True)

    listing = models.OneToOneField(
        "Listing",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=listing_cover_image_path, null=True, blank=True)

    large = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=555),
                              upload_to=listing_cover_image_path, null=True, blank=True)

    medium = models.ImageField(storage=
                               ThumbnailImageStorage(target_width=767, target_height=275),
                               upload_to=listing_cover_image_path, null=True, blank=True)

    small = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=180),
                              upload_to=listing_cover_image_path, null=True, blank=True)


    class Meta:
        db_table = TABLE_PREFIX + 'listing_cover_image'


class ListingPreviewImage(ListingImage):
    listing = models.ForeignKey(
        "Listing",
        on_delete=models.CASCADE
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=listing_preview_image_path, null=True, blank=True)

    large = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=555),
                              upload_to=listing_preview_image_path, null=True, blank=True)

    medium = models.ImageField(storage=
                               ThumbnailImageStorage(target_width=767, target_height=275),
                               upload_to=listing_preview_image_path, null=True, blank=True)

    small = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=180),
                              upload_to=listing_preview_image_path, null=True, blank=True)

    index = models.IntegerField(default=0)
    caption = models.CharField(max_length=300, blank=True)


    class Meta:
        db_table = TABLE_PREFIX + 'listing_preview_image'
        ordering = ['index']
