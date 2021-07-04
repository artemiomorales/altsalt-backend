import graphene
from graphene_django.types import DjangoObjectType
from catalog.models.collection import *
from django.template.defaultfilters import slugify
from .schema_base import BaseImageTypeMixin


class CollectionBylineType(DjangoObjectType):
    class Meta:
        model = CollectionByline


class CollectionCoverImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = CollectionCoverImage


class CollectionDedicationImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = CollectionDedicationImage


class CollectionArticleType(DjangoObjectType):
    class Meta:
        model = CollectionArticle


class CollectionListingType(DjangoObjectType):
    class Meta:
        model = CollectionListing


class CollectionAdditionalResourcesType(DjangoObjectType):
    class Meta:
        model = CollectionAdditionalResources


class CollectionType(DjangoObjectType):
    slug = graphene.String()
    bylines = graphene.List(CollectionBylineType)
    cover_image = graphene.Field(CollectionCoverImageType)
    dedication_image = graphene.Field(CollectionDedicationImageType)
    articles = graphene.List(CollectionArticleType)
    listings = graphene.List(CollectionListingType)
    additional_resources = graphene.List(CollectionAdditionalResourcesType)

    def resolve_slug(self, info):
        return slugify(self.title) + '-' + slugify(self.subtitle)

    def resolve_cover_image(self, info):
        if CollectionCoverImage.objects.filter(collection=self).exists():
            return CollectionCoverImage.objects.get(collection=self)
        else:
            return None

    def resolve_dedication_image(self, info):
        if CollectionDedicationImage.objects.filter(collection=self).exists():
            return CollectionDedicationImage.objects.get(collection=self)
        else:
            return None

    def resolve_bylines(self, info, **kwargs):
        return CollectionByline.objects.filter(collection_id=self.id)

    def resolve_articles(self, info, **kwargs):
        return CollectionArticle.objects.filter(collection_id=self.id).order_by('collection_priority')

    def resolve_listings(self, info, **kwargs):
        return CollectionListing.objects.filter(collection_id=self.id).order_by('collection_priority')

    def resolve_additional_resources(self, info, **kwargs):
        return CollectionAdditionalResources.objects.filter(collection_id=self.id).order_by('collection_priority')

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