from django.db import models

from .base import TABLE_PREFIX, CustomImageAlttext, article_cover_image_path
from .user import User
from django.template.defaultfilters import slugify

from catalog.backends import ThumbnailImageStorage

from django import utils


class EditorialSettings(models.Model):
    show_newsletter_popup = models.BooleanField(default=True)
    show_featured = models.BooleanField(default=True)
    featured_heading = models.CharField(default="Featured", max_length=180)

    def __str__(self):
        return "Editorial Settings"

    def save(self, *args, **kwargs):
        if EditorialSettings.objects.exists() and EditorialSettings.objects.get(id=self.id) is None:
            raise ValueError("This model has already its record.")
        else:
            super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Editorial Settings'
        verbose_name_plural = 'Editorial Settings'


class Article(models.Model):
    title = models.CharField(max_length=125)
    seo_title = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(unique=True, blank=True)
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


class ArticleFeaturedImage(CustomImageAlttext):

    article = models.OneToOneField(
        "Article",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=article_cover_image_path, null=True, blank=True)

    large = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=555),
                              upload_to=article_cover_image_path, null=True, blank=True)

    medium = models.ImageField(storage=
                               ThumbnailImageStorage(target_width=767, target_height=275),
                               upload_to=article_cover_image_path, null=True, blank=True)

    small = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=767, target_height=180),
                              upload_to=article_cover_image_path, null=True, blank=True)

    caption = models.CharField(max_length=300, blank=True)