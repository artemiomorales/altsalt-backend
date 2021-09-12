import graphene
from catalog.models.playlist import *
from .schema_base import BaseImageTypeMixin, GenericImageType, LinkType
from .schema_user import UserType
from graphene_django.types import DjangoObjectType
from django.template.defaultfilters import slugify


class PlaylistCoverImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = PlaylistCoverImage


class PlaylistEntryType(DjangoObjectType):
    class Meta:
        model = PlaylistEntry

    content_id = graphene.ID()
    type = graphene.String()
    title = graphene.String()
    content_summary = graphene.String()
    description = graphene.String()
    slug = graphene.String()
    cover_image = graphene.Field(GenericImageType)
    availability = graphene.List(LinkType)
    has_upload = graphene.Boolean()
    download_url = graphene.String()
    authors = graphene.List(UserType)

    def resolve_content_id(self, info):
        return self.get_content_id()

    def resolve_type(self, info):
        return self.get_type()

    def resolve_title(self, info):
        return self.get_title()

    def resolve_slug(self, info):
        return slugify(self.get_title())

    def resolve_cover_image(self, info):
        return self.get_cover_image()

    def resolve_content_summary(self, info):
        return self.get_content_summary()

    def resolve_description(self, info):
        return self.get_description()

    def resolve_availability(self, info):
        return self.get_availability()

    def resolve_has_upload(self, info):
        return self.get_has_upload()

    def resolve_download_url(self, info):
        return self.get_download_url()

    def resolve_authors(self, info):
        return self.get_authors()


class PlaylistType(DjangoObjectType):
    slug = graphene.String()
    cover_image = graphene.Field(PlaylistCoverImageType)
    entries = graphene.List(PlaylistEntryType)

    def resolve_slug(self, info):
        return slugify(self.__str__())

    def resolve_cover_image(self, info):
        if PlaylistCoverImage.objects.filter(playlist=self).exists():
            return PlaylistCoverImage.objects.get(playlist=self)
        else:
            return None

    def resolve_entries(self, info):
        return PlaylistEntry.objects.filter(playlist_id=self.id)

    class Meta:
        model = Playlist


class PlaylistQuery(graphene.ObjectType):
    playlist = graphene.Field(PlaylistType, id=graphene.String())
    playlist_bundle = graphene.List(PlaylistType)

    def resolve_playlist(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Playlist.objects.get(id=int(id))

        return None

    def resolve_playlist_bundle(self, info, **kwargs):
        # include_featured = kwargs.get('include_featured')
        # exclude_private = kwargs.get('exclude_private')
        # approved_after_date = kwargs.get('approved_after_date')
        # approved_before_date = kwargs.get('approved_before_date')
        #
        # if include_featured is True:
        #     listings = Listing.objects.all()
        # else:
        #     listings = Listing.objects.filter(is_featured=False)
        #
        # if exclude_private is True:
        #     listings = listings.filter(is_published=True, is_approved=True)
        #
        # if approved_after_date is not None:
        #     listings = listings.filter(date_approved__gte=approved_after_date)
        #
        # if approved_before_date is not None:
        #     listings = listings.filter(date_approved__lt=approved_before_date)

        return Playlist.objects.all()