from .base import \
    TABLE_PREFIX, PublishStatus, CustomImageAlttext, playlist_cover_image_path, CustomSaveMixin
from catalog.backends import ThumbnailImageStorage
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from catalog.models.cms import Article, ArticleFeaturedImage, ArticleByline
from catalog.models.art import Art, ArtUpload, ArtByline
from catalog.models.movie import Movie, MovieCoverImage, MovieByline
from catalog.models.listing import Listing, ListingCoverImage, ListingAvailabilityLink, ListingUpload,\
    ListingCreatorByline, ListingCollaboratorByline, ListingFormat
from django.db import models


class Playlist(models.Model):
    title = models.CharField(default="", max_length=100)
    subtitle = models.CharField(default="", max_length=100, blank=True)
    description = models.TextField(default="", blank=True)

    publish_status = models.CharField(
        max_length=2,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )

    def __str__(self):
        return "{0}".format(self.title)

    class Meta:
        db_table = TABLE_PREFIX + 'playlist'


class PlaylistCoverImage(CustomImageAlttext):
    playlist = models.OneToOneField(
        "Playlist",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=playlist_cover_image_path, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'playlist_cover_image'


class PlaylistEntry(CustomSaveMixin):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    playlist = models.ForeignKey("Playlist", on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    def get_content_id(self):
        return self.object_id

    def is_valid_content(self, skip_exception=False):
        model = self.content_type.model_class()

        if model is Listing or model is Article or model is Art or model is Movie:
            return True
        else:
            if not skip_exception:
                raise Exception("Invalid content type specified for playlist entry")
        return False

    def get_type(self):
        model = self.content_type.model_class()

        if model is Listing:
            return 'listing'

        if model is Article:
            return 'article'

        if model is Art:
            return 'art'

        if model is Movie:
            return 'movie'

        raise Exception("Invalid content type specified for playlist entry")

    def get_title(self):

        if self.is_valid_content():
            return '{0}'.format(self.content_object.title)

    def get_content_summary(self):
        model = self.content_type.model_class()

        if model is Listing:
            if ListingFormat.objects.filter(listing_id=self.content_object.id).exists():
                return ListingFormat.objects.filter(listing_id=self.content_object.id).first()
            return ''

        if model is Article:
            return 'post'

        if model is Art:
            return 'artwork'

        if model is Movie:
            return 'movie'

        raise Exception("Invalid content type specified for playlist entry")

    def get_description(self):

        if self.is_valid_content():
            model = self.content_type.model_class()
            if model is Listing or model is Art or model is Movie:
                return '{0}'.format(self.content_object.description)
            elif model is Article:
                return '{0}'.format(self.content_object.preview_text)

    def get_cover_image(self):

        if self.is_valid_content():
            model = self.content_type.model_class()

            if model is Listing:
                if ListingCoverImage.objects.filter(listing_id=self.content_object.id).exists():
                    return ListingCoverImage.objects.get(listing_id=self.content_object.id)
            elif model is Article:
                if ArticleFeaturedImage.objects.filter(article_id=self.content_object.id).exists():
                    return ArticleFeaturedImage.objects.get(article_id=self.content_object.id)
            elif model is Art:
                if ArtUpload.objects.filter(art_id=self.content_object.id).exists():
                    return ArtUpload.objects.filter(art_id=self.content_object.id).first()
            elif model is Movie:
                if MovieCoverImage.objects.filter(movie_id=self.content_object.id).exists():
                    return MovieCoverImage.objects.get(movie_id=self.content_object.id)

            return None

    def get_availability(self):

        if self.is_valid_content():
            model = self.content_type.model_class()
            link_array = []

            if model is Listing and ListingAvailabilityLink.objects.filter(listing_id=self.content_object.id).exists():
                listing_availability_links = ListingAvailabilityLink.objects.filter(listing_id=self.content_object.id)
                for link in listing_availability_links:
                    link_array.append({
                        'id': link.id,
                        'name': link.name,
                        'url': link.url
                    })

                import logging
                logging.error(link_array)

                return link_array

            return None

    def get_has_upload(self):
        model = self.content_type.model_class()

        if model is Listing and ListingUpload.objects.filter(listing_id=self.content_object.id).exists():
            listing_upload = ListingUpload.objects.get(listing_id=self.content_object.id)
            if listing_upload.file.name:
                return True

        return False

    def get_download_url(self):
        model = self.content_type.model_class()

        if model is Listing and ListingUpload.objects.filter(listing_id=self.content_object.id).exists():
            listing_upload = ListingUpload.objects.get(listing_id=self.content_object.id)
            if listing_upload.allow_downloads and listing_upload.file.name:
                return listing_upload.file.url

        return None

    def get_authors(self):
        if self.is_valid_content():
            model = self.content_type.model_class()

            authors = []

            if model is Listing:
                if ListingCreatorByline.objects.filter(listing_id=self.content_object.id).exists():
                    creator_bylines = ListingCreatorByline.objects.filter(listing_id=self.content_object.id, is_confirmed=True)\
                        .order_by('listing_priority')
                    for byline in creator_bylines:
                        authors.append(byline.user)
                if ListingCollaboratorByline.objects.filter(listing_id=self.content_object.id).exists():
                    collaborator_bylines = ListingCollaboratorByline.objects.filter(listing_id=self.content_object.id, is_confirmed=True)\
                        .order_by('listing_priority')
                    for byline in collaborator_bylines:
                        authors.append(byline.user)
                return authors

            if model is Article:
                if ArticleByline.objects.filter(article_id=self.content_object.id).exists():
                    creator_bylines = ArticleByline.objects.filter(article_id=self.content_object.id, is_confirmed=True)\
                        .order_by('article_priority')
                    for byline in creator_bylines:
                        authors.append(byline.user)
                return authors

            if model is Art:
                if ArtByline.objects.filter(art_id=self.content_object.id).exists():
                    creator_bylines = ArtByline.objects.filter(art_id=self.content_object.id, is_confirmed=True)\
                        .order_by('art_priority')
                    for byline in creator_bylines:
                        authors.append(byline.user)
                return authors

            if model is Movie:
                if MovieByline.objects.filter(movie_id=self.content_object.id).exists():
                    creator_bylines = MovieByline.objects.filter(movie_id=self.content_object.id, is_confirmed=True)\
                        .order_by('movie_priority')
                    for byline in creator_bylines:
                        authors.append(byline.user)
                return authors

    def save(self, skip_callback=False, *args, **kwargs):

        if self.is_valid_content():
            super().save(*args, **kwargs)

    def __str__(self):
        if self.is_valid_content(True):
            return self.content_object.title
        return "Invalid content"

    class Meta:
        ordering = ['priority']
        db_table = TABLE_PREFIX + 'playlist_entry'