from django.db import models
from django.conf import settings
import datetime

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


def profile_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'catalog/user_{0}/{1}'.format(instance, filename)


def listing_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    date = datetime.datetime.now()
    return 'catalog/images/{0}/{1}-{2}'. format(date.strftime("%m%d%y"), date.strftime("%f"), filename)