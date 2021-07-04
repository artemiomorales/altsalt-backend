from .base import \
    TABLE_PREFIX, PublishStatus, CustomImageAlttext, collection_cover_image_path
from .user import User
from django.db import models
from catalog.backends import ThumbnailImageStorage
from catalog.models.cms import Article
from catalog.models.listing import Listing


class Collection(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=100, blank=True)
    description = models.TextField(default="", blank=True)
    dedication = models.TextField(default="", blank=True)

    publish_status = models.CharField(
        max_length=2,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'collection'


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


class CollectionDedicationImage(CustomImageAlttext):
    collection = models.OneToOneField(
        "Collection",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=collection_cover_image_path, null=True, blank=True)

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


class CollectionArticle(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    collection_priority = models.IntegerField(default=0)
    article_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_article'
        constraints = [
            models.UniqueConstraint(fields=['collection', 'article'], name='collection_article_link')
        ]


class CollectionListing(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    collection_priority = models.IntegerField(default=0)
    listing_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_listing'
        constraints = [
            models.UniqueConstraint(fields=['collection', 'listing'], name='collection_listing_link')
        ]


class CollectionAdditionalResources(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    collection_priority = models.IntegerField(default=0)
    article_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'collection_additional_resources'
        constraints = [
            models.UniqueConstraint(fields=['collection', 'article'], name='collection_additional_resources_link')
        ]
