import graphene
from graphene_django.types import DjangoObjectType
from catalog.models.collection import *
from django.template.defaultfilters import slugify
from .schema_base import BaseImageTypeMixin
from django.db import models
from catalog.schema.schema_user import UserType



class CollectionBylineType(DjangoObjectType):
    class Meta:
        model = CollectionByline


class CollectionCoverImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = CollectionCoverImage


class CollectionIntroImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = CollectionIntroImage


class CollectionDedicationImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = CollectionDedicationImage


class DjangoImageFieldType(graphene.ObjectType):
    url = graphene.String()
    width = graphene.Int()
    height = graphene.Int()

    def resolve_url(self, info):
        return self.url

    def resolve_width(self, info):
        return self.width

    def resolve_height(self, info):
        return self.height


class GenericImageType(graphene.ObjectType):
    id = graphene.ID()
    alttext = graphene.String()
    original = graphene.Field(DjangoImageFieldType)

    def resolve_id(self, info):
        return self.id

    def resolve_alttext(self, info):
        return self.alttext

    def resolve_original(self, info):
        return self.original


class LinkType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    url = graphene.Field(DjangoImageFieldType)

    def resolve_id(self, info):
        return self.id

    def resolve_name(self, info):
        return self.name

    def resolve_url(self, info):
        return self.url


class PageSectionEntryType(DjangoObjectType):
    class Meta:
        model = PageSectionEntry

    content_id = graphene.ID()
    type = graphene.String()
    title = graphene.String()
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

    def resolve_availability(self, info):
        return self.get_availability()

    def resolve_has_upload(self, info):
        return self.get_has_upload()

    def resolve_download_url(self, info):
        return self.get_download_url()

    def resolve_authors(self, info):
        return self.get_authors()


class PageSectionType(DjangoObjectType):
    class Meta:
        model = PageSection

    entries = graphene.List(PageSectionEntryType)

    def resolve_entries(self, info):
        return PageSectionEntry.objects.filter(page_section_id=self.id)


class CollectionPageSectionType(DjangoObjectType):
    class Meta:
        model = CollectionPageSection
        exclude = ('page_section',)

    page_section = graphene.Field(PageSectionType)

    def resolve_page_section(self, info):
        return PageSection.objects.get(id=self.page_section_id)


class CollectionType(DjangoObjectType):
    slug = graphene.String()
    bylines = graphene.List(CollectionBylineType)
    cover_image = graphene.Field(CollectionCoverImageType)
    intro_image = graphene.Field(CollectionIntroImageType)
    dedication_image = graphene.Field(CollectionDedicationImageType)
    page_section_set = graphene.List(CollectionPageSectionType)

    def resolve_slug(self, info):
        return slugify(self.__str__())

    def resolve_cover_image(self, info):
        if CollectionCoverImage.objects.filter(collection=self).exists():
            return CollectionCoverImage.objects.get(collection=self)
        else:
            return None

    def resolve_intro_image(self, info):
        if CollectionIntroImage.objects.filter(collection=self).exists():
            return CollectionIntroImage.objects.get(collection=self)
        else:
            return None

    def resolve_page_section_set(self, info):
        return CollectionPageSection.objects.filter(collection_id=self.id)

    def resolve_dedication_image(self, info):
        if CollectionDedicationImage.objects.filter(collection=self).exists():
            return CollectionDedicationImage.objects.get(collection=self)
        else:
            return None

    def resolve_bylines(self, info, **kwargs):
        return CollectionByline.objects.filter(collection_id=self.id)


    class Meta:
        model = Collection



class CollectionQuery(graphene.ObjectType):
    collection = graphene.Field(CollectionType, id=graphene.String())
    collection_bundle = graphene.List(CollectionType)

    def resolve_collection(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Collection.objects.get(id=int(id))

        return None

    def resolve_collection_bundle(self, info, **kwargs):
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

        return Collection.objects.all()