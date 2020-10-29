from .base import PROJECT_PREFIX, TABLE_PREFIX, media_upload_path, listing_cover_image_path, listing_preview_image_path
from .user import *
from django.db import models


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_image')
    name = models.CharField(max_length=50, blank=True)
    url = models.ImageField(upload_to=media_upload_path)
    caption = models.CharField(max_length=300, blank=True)
    alttext = models.CharField(max_length=300)
    original = models.ImageField(upload_to=media_upload_path, null=True, blank=True)
    large = models.ImageField(upload_to=media_upload_path, null=True, blank=True)
    medium = models.ImageField(upload_to=media_upload_path, null=True, blank=True)
    small = models.ImageField(upload_to=media_upload_path, null=True, blank=True)

    def __str__(self):
        return self.url.__str__()

    class Meta:
        db_table = TABLE_PREFIX + 'image'
