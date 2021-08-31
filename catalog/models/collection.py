from .base import \
    TABLE_PREFIX, PublishStatus, CustomImageAlttext, collection_cover_image_path, \
    collection_intro_image_path, collection_dedication_image_path, CustomSaveMixin
from .user import User
from django.db import models
from catalog.backends import ThumbnailImageStorage
from catalog.models.cms import Article, ArticleFeaturedImage, ArticleByline
from catalog.models.listing import Listing, ListingCoverImage, ListingAvailabilityLink, ListingUpload,\
    ListingCreatorByline, ListingCollaboratorByline
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class Collection(models.Model):
    title1 = models.CharField(default="", max_length=100, blank=True)
    title2 = models.CharField(default="", max_length=100, blank=True)
    title3 = models.CharField(default="", max_length=100, blank=True)
    introduction = models.TextField(default="", blank=True)
    intro_font_color = models.CharField(default="", max_length=100, blank=True)
    intro_background_color = models.CharField(default="", max_length=100, blank=True)
    dedication = models.TextField(default="", blank=True)
    page_section = models.ManyToManyField(
        "PageSection",
        through='CollectionPageSection'
    )

    publish_status = models.CharField(
        max_length=2,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )

    def __str__(self):
        return "{0} {1} {2}".format(self.title1, self.title2, self.title3)

    class Meta:
        db_table = TABLE_PREFIX + 'collection'


class CollectionPageSection(models.Model):
    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="collection")
    page_section = models.ForeignKey("PageSection", on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    hide_header = models.BooleanField(default=False)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_page_section'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['collection', 'page_section'], name='collection_page_section_link')
        ]


class PageSection(models.Model):
    title = models.CharField(default="", max_length=100, blank=True)
    description = models.TextField(default="", blank=True)

    def __str__(self):

        collection_titles = ""

        if CollectionPageSection.objects.filter(page_section=self).exists():
            collection_page_sections = CollectionPageSection.objects.filter(page_section=self)
            for item in collection_page_sections:
                collection_titles += (item.collection.__str__() + ', ')

        if self.title != "":
            return "{0} - {1}".format(self.title, collection_titles)

        else:
            return "{0} {1}".format("Untitled", self.id)

    class Meta:
        db_table = TABLE_PREFIX + 'page_section'


class PageSectionEntry(CustomSaveMixin):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    page_section = models.ForeignKey("PageSection", on_delete=models.CASCADE)
    subtitle = models.CharField(max_length=100, blank=True)
    description = models.TextField(default="", blank=True)
    priority = models.IntegerField(default=0)

    class Layout(models.TextChoices):
        ONE_COLUMN = 'one-column', _('One Column')
        TWO_COLUMN = 'two-column', _('Two Column')

    desktop_layout = models.CharField(
        max_length=10,
        choices=Layout.choices,
        default=Layout.ONE_COLUMN,
    )

    def get_content_id(self):
        return self.object_id

    def is_valid_content(self, skip_exception=False):
        model = self.content_type.model_class()

        if model is Listing or model is Article:
            return True
        else:
            if not skip_exception:
                raise Exception("Invalid content type specified for page section entry on collection")
        return False

    def get_type(self):
        model = self.content_type.model_class()

        if model is Listing:
            return 'listing'

        if model is Article:
            return 'article'

        raise Exception("Invalid content type specified for page section entry on collection")

    def get_title(self):

        if self.is_valid_content():
            return '{0}'.format(self.content_object.title)

    def get_cover_image(self):

        if self.is_valid_content():
            model = self.content_type.model_class()

            if model is Listing:
                if ListingCoverImage.objects.filter(listing_id=self.content_object.id):
                    return ListingCoverImage.objects.get(listing_id=self.content_object.id)
            elif model is Article:
                if ArticleFeaturedImage.objects.filter(article_id=self.content_object.id):
                    return ArticleFeaturedImage.objects.get(article_id=self.content_object.id)

            return None

    def get_availability(self):

        if self.is_valid_content():
            model = self.content_type.model_class()
            link_array = []

            if model is Listing and ListingAvailabilityLink.objects.filter(listing_id=self.content_object.id).exists():
                listing_availability_links = ListingAvailabilityLink.objects.filter(listing_id=self.content_object.id)
                for link in listing_availability_links:
                    link_array.append({
                        'id': link.id,
                        'name': link.name,
                        'url': link.url
                    })
                return link_array

    def get_has_upload(self):
        model = self.content_type.model_class()

        if model is Listing and ListingUpload.objects.filter(listing_id=self.content_object.id).exists():
            listing_upload = ListingUpload.objects.get(listing_id=self.content_object.id)
            if listing_upload.file.name:
                return True

        return False

    def get_download_url(self):
        model = self.content_type.model_class()

        if model is Listing and ListingUpload.objects.filter(listing_id=self.content_object.id).exists():
            listing_upload = ListingUpload.objects.get(listing_id=self.content_object.id)
            if listing_upload.allow_downloads and listing_upload.file.name:
                return listing_upload.file.url

        return None

    def get_authors(self):
        if self.is_valid_content():
            model = self.content_type.model_class()

            authors = []
            import logging
            logging.error("we are here")
            if model is Listing:
                if ListingCreatorByline.objects.filter(listing_id=self.content_object.id).exists():
                    creator_bylines = ListingCreatorByline.objects.filter(listing_id=self.content_object.id, is_confirmed=True)\
                        .order_by('listing_priority')
                    logging.error(creator_bylines)
                    for byline in creator_bylines:
                        authors.append(byline.user)
                if ListingCollaboratorByline.objects.filter(listing_id=self.content_object.id).exists():
                    collaborator_bylines = ListingCollaboratorByline.objects.filter(listing_id=self.content_object.id, is_confirmed=True)\
                        .order_by('listing_priority')
                    for byline in collaborator_bylines:
                        authors.append(byline.user)
                return authors

            if model is Article:
                if ArticleByline.objects.filter(article_id=self.content_object.id).exists():
                    creator_bylines = ArticleByline.objects.filter(article_id=self.content_object.id, is_confirmed=True)\
                        .order_by('article_priority')
                    for byline in creator_bylines:
                        authors.append(byline.user)
                return authors

    def save(self, skip_callback=False, *args, **kwargs):

        if self.is_valid_content():
            super().save(*args, **kwargs)

    def __str__(self):
        if self.is_valid_content(True):
            return self.content_object.title
        return "Invalid content"

    class Meta:
        db_table = TABLE_PREFIX + 'page_section_entry'


class CollectionCoverImage(CustomImageAlttext):
    collection = models.OneToOneField(
        "Collection",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=collection_cover_image_path, null=True, blank=True)

    caption = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_cover_image'


class CollectionIntroImage(CustomImageAlttext):
    collection = models.OneToOneField(
        "Collection",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=collection_intro_image_path, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_intro_image'


class CollectionDedicationImage(CustomImageAlttext):
    collection = models.OneToOneField(
        "Collection",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=collection_dedication_image_path, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_dedication_image'


class CollectionByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    collection_priority = models.IntegerField(default=0)
    is_confirmed = models.BooleanField(default=False)
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="collection_byline_requester", blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_byline'
        ordering = ['-collection_priority']
        constraints = [
            models.UniqueConstraint(fields=['user', 'collection'], name='user_collection_link')
        ]
