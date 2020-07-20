from .base import PROJECT_PREFIX, TABLE_PREFIX, listing_directory_path
from .user import *
from django.db import models


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, blank=True)
    url = models.ImageField(upload_to=listing_directory_path)
    caption = models.CharField(max_length=300, blank=True)
    alttext = models.CharField(max_length=300)

    def __str__(self):
        return self.url.__str__()

    class Meta:
        db_table = TABLE_PREFIX + 'image'


class ListingCoverImage(models.Model):
    listing = models.OneToOneField(
        "Listing",
        primary_key=True,
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(Image, on_delete=models.CASCADE)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_cover_image'


class ListingPreviewImage(models.Model):
    listing = models.ForeignKey("Listing", on_delete=models.CASCADE, related_name="listings")
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_preview_image'
        constraints = [
            models.UniqueConstraint(fields=['listing', 'image'], name='listing_preview_image_link')
        ]