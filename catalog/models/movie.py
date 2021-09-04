from django.db import models
from .base import \
    TABLE_PREFIX, movie_upload_path, CustomImageAlttext, Country, Identity, \
    Genre, Tag, PublishStatus
from .user import User
from catalog.backends import CatalogImageStorage, ThumbnailImageStorage


class Movie(models.Model):
    title = models.CharField(max_length=125)
    description = models.TextField(default="", blank=True)
    is_featured = models.BooleanField(default=False)
    content_rating = models.ForeignKey("ContentRating", null=True, blank=True, on_delete=models.PROTECT)
    src_1080 = models.CharField(max_length=500)
    src_720 = models.CharField(max_length=500)
    src_360 = models.CharField(max_length=500)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    playtime = models.FloatField(default=0)

    publish_status = models.CharField(
        max_length=2,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'movie'


class MovieByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    movie_priority = models.IntegerField(default=0)
    is_confirmed = models.BooleanField(default=False)
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="movie_byline_requester", blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'movie_byline'
        constraints = [
            models.UniqueConstraint(fields=['user', 'movie'], name='user_movie_link')
        ]


class MovieCoverImage(CustomImageAlttext):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE)
    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=movie_upload_path, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'movie_cover_image'


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'movie_genre'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['movie', 'genre'], name='movie_genre_link')
        ]


class MovieCountryRepresented(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'movie_country_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['movie', 'country'], name='movie_country_link')
        ]


class MovieIdentityRepresented(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'movie_identity_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['movie', 'identity'], name='movie_identity_link')
        ]


class MovieTag(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'movie_tag'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['movie', 'tag'], name='movie_tag_link')
        ]