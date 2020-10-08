import os
import datetime
import logging

from django.db import models
from django.conf import settings
from django.template.defaultfilters import slugify

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


class Continent(NameSlug):

    class Meta:
        db_table = TABLE_PREFIX + 'continent'


class Culture(NameSlug):
    continent = models.ForeignKey(Continent, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'culture'


def user_media_path(user_id):
    return 'catalog/user/{0}'.format(user_id)


def profile_image_path(instance, filename):
    date = datetime.datetime.now()
    filename, file_extension = os.path.splitext(filename)
    save_string = (user_media_path(instance.user.id) + "/profile-image/{0}-{1}{2}").format(filename, date.strftime("%f"), file_extension)

    return save_string


def media_upload_path(instance, filename):
    date = datetime.datetime.now()
    return (user_media_path(instance.user_id) + "/uploads/{0}-{1}").format(date.strftime("%f"), filename)
