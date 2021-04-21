from django.db import models

from .base import TABLE_PREFIX, CustomImageAlttext, article_cover_image_path, \
    Identity, Country, Format, DistributionType, Length, Genre, Language, Tag, \
    Price, ContentRating
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
    seo_title = models.CharField(default="", max_length=125, blank=True)
    preview_text = models.TextField(max_length=200)
    body = models.TextField(default="")
    post_script = models.TextField(default="", blank=True)
    creation_date = models.DateField(default=utils.timezone.now)
    publish_date = models.DateField(default=utils.timezone.now)
    is_published = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_full_bleed = models.BooleanField(default=False)
    is_excerpt = models.BooleanField(default=False)
    length = models.ForeignKey("Length", null=True, blank=True, on_delete=models.PROTECT)
    price = models.ForeignKey("Price", null=True, blank=True, on_delete=models.SET_NULL)
    content_rating = models.ForeignKey("ContentRating", null=True, blank=True, on_delete=models.PROTECT)
    related_publish_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-publish_date']
        db_table = TABLE_PREFIX + 'article'


class ArticleByline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    user_priority = models.IntegerField(default=0)
    article_priority = models.IntegerField(default=0)
    is_confirmed = models.BooleanField(default=False)
    requester = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="article_byline_requester", blank=True)

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


class ArticleFormat(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name="article")
    format = models.ForeignKey(Format, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_format'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['article', 'format'], name='article_format_link')
        ]


class ArticleDistributionType(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    distribution_type = models.ForeignKey(DistributionType, on_delete=models.CASCADE)

    class Meta:
        db_table = TABLE_PREFIX + 'article_distribution_type'
        constraints = [
            models.UniqueConstraint(fields=['article', 'distribution_type'], name='article_distribution_type_link')
        ]


class ArticleGenre(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_genre'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['article', 'genre'], name='article_genre_link')
        ]


class ArticleLanguage(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_language'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['article', 'language'], name='article_language_link')
        ]


class ArticleCountryRepresented(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_country_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['article', 'country'], name='article_country_link')
        ]


class ArticleIdentityRepresented(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_identity_represented'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['article', 'identity'], name='article_identity_link')
        ]


class ArticleTag(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'article_tag'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['article', 'tag'], name='article_tag_link')
        ]