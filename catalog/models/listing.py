from .base import PROJECT_PREFIX, TABLE_PREFIX, listing_cover_image_path, listing_preview_image_path, Link, NameSlug, Culture
from .user import *
from .image import Image

from django.db import models
from django.template.defaultfilters import slugify


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
    is_approved = models.BooleanField(null=True)
    date_approved = models.DateField(null=True)
    is_published = models.BooleanField(null=True)
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
    class Meta:
        db_table = TABLE_PREFIX + 'length'


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

    class Meta:
        abstract = True


class ListingCoverImage(ListingImage):
    listing = models.OneToOneField(
        "Listing",
        primary_key=True,
        on_delete=models.CASCADE
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=listing_cover_image_path, null=True, blank=True)

    large = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=555, save_thumbnails=True),
                              upload_to=listing_cover_image_path, null=True, blank=True)

    medium = models.ImageField(storage=
                               ThumbnailImageStorage(target_width=767, target_height=275, save_thumbnails=True),
                               upload_to=listing_cover_image_path, null=True, blank=True)

    small = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=180, save_thumbnails=True),
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
                              ThumbnailImageStorage(target_width=767, target_height=555, save_thumbnails=True),
                              upload_to=listing_preview_image_path, null=True, blank=True)

    medium = models.ImageField(storage=
                               ThumbnailImageStorage(target_width=767, target_height=275, save_thumbnails=True),
                               upload_to=listing_preview_image_path, null=True, blank=True)

    small = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=180, save_thumbnails=True),
                              upload_to=listing_preview_image_path, null=True, blank=True)

    index = models.IntegerField(default=0)
    caption = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_preview_image'
        ordering = ['index']
