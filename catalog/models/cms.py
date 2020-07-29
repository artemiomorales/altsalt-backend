import datetime
from django.db import models

from .base import PROJECT_PREFIX, TABLE_PREFIX
from .image import Image
from .user import *
from django.template.defaultfilters import slugify

from django import utils


class Article(models.Model):
    title = models.CharField(max_length=100)
    seo_title = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    featured_image = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    preview_text = models.TextField(max_length=200)
    body = models.TextField()
    creation_date = models.DateField(default=utils.timezone.now)
    publish_date = models.DateField(default=utils.timezone.now)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.seo_title = self.title
            self.slug = slugify(self.title)

        super(Article, self).save(*args, **kwargs)

    class Meta:
        db_table = TABLE_PREFIX + 'article'


class ArticleByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    article_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_byline'
        constraints = [
            models.UniqueConstraint(fields=['user', 'article'], name='user_article_link')
        ]