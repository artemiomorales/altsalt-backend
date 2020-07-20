from .base import PROJECT_PREFIX, TABLE_PREFIX
from .user import *
from .image import *

from django.db import models
from django.template.defaultfilters import slugify


class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    preview_images = models.ManyToManyField(
        "Image",
        through='ListingPreviewImage'
    )
    format = models.ManyToManyField(
        "Format",
        through='ListingFormat'
    )
    distribution_type = models.ManyToManyField(
        "DistributionType",
        through='ListingDistributionType'
    )
    length = models.ForeignKey("Length", on_delete=models.PROTECT)
    genre = models.ManyToManyField(
        "Genre",
        through='ListingGenre'
    )
    language = models.ManyToManyField(
        "Language",
        through='ListingLanguage'
    )
    publication_date = models.DateField()
    date_added = models.DateField()
    is_approved = models.BooleanField()
    is_published = models.BooleanField()

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.title)

        super(Listing, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'listing'


class ListingCreationByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    listing_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_creation_byline'
        constraints = [
            models.UniqueConstraint(fields=['user', 'listing'], name='user_listing_creation_link')
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


class ListingInfo(models.Model):
    name = models.CharField(max_length=55, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.name)

        super(ListingInfo, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Format(ListingInfo):
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


class DistributionType(ListingInfo):
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


class Length(ListingInfo):
    class Meta:
        db_table = TABLE_PREFIX + 'length'


class Genre(ListingInfo):
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


class Language(ListingInfo):
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