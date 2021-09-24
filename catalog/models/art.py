from django.db import models
from .base import \
    TABLE_PREFIX, art_upload_path, CustomImageAlttext, Country, Identity, \
    Genre, Tag, PublishStatus
from .user import User
from catalog.backends import CatalogImageStorage, ThumbnailImageStorage


class Art(models.Model):
    title = models.CharField(max_length=125)
    description = models.TextField(default="", blank=True)
    is_featured = models.BooleanField(default=False)
    hide_bylines = models.BooleanField(default=False)
    show_custom_author = models.BooleanField(default=False)
    custom_author = models.CharField(max_length=150, blank=True)
    content_rating = models.ForeignKey("ContentRating", null=True, blank=True, on_delete=models.PROTECT)

    publish_status = models.CharField(
        max_length=2,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'art'


class ArtByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    art_priority = models.IntegerField(default=0)
    is_confirmed = models.BooleanField(default=False)
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="art_byline_requester", blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'art_byline'
        constraints = [
            models.UniqueConstraint(fields=['user', 'art'], name='user_art_link')
        ]


class ArtUpload(CustomImageAlttext):
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=art_upload_path, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'art_upload'


class ArtGenre(models.Model):
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'art_genre'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['art', 'genre'], name='art_genre_link')
        ]


class ArtCountryRepresented(models.Model):
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'art_country_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['art', 'country'], name='art_country_link')
        ]


class ArtIdentityRepresented(models.Model):
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'art_identity_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['art', 'identity'], name='art_identity_link')
        ]


class ArtTag(models.Model):
    art = models.ForeignKey(Art, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'art_tag'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['art', 'tag'], name='art_tag_link')
        ]