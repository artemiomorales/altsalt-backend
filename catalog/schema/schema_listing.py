from catalog.models import *

import graphene
from graphene_django.types import DjangoObjectType
from .schema_image import ImageType


class ListingCreationBylineType(DjangoObjectType):
    class Meta:
        model = ListingCreationByline


class ListingCollaboratorBylineType(DjangoObjectType):
    class Meta:
        model = ListingCollaboratorByline


class ListingAvailabilityLinkType(DjangoObjectType):
    class Meta:
        model = ListingAvailabilityLink


class ListingAdditionalLinkType(DjangoObjectType):
    class Meta:
        model = ListingAdditionalLink


class FormatType(DjangoObjectType):
    class Meta:
        model = Format


class ListingFormatType(DjangoObjectType):
    class Meta:
        model = ListingFormat
        exclude = ('format',)

    item = graphene.Field(FormatType)

    def resolve_item(self, info):
        return Format.objects.get(id=self.format_id)

class DistributionTypeType(DjangoObjectType):
    class Meta:
        model = DistributionType


class ListingDistributionTypeType(DjangoObjectType):
    class Meta:
        model = ListingDistributionType
        exclude = ('distribution_type',)

    item = graphene.Field(DistributionTypeType)

    def resolve_item(self, info):
        return DistributionType.objects.get(id=self.distribution_type_id)


class LengthType(DjangoObjectType):
    class Meta:
        model = Length


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre


class ListingGenreType(DjangoObjectType):
    class Meta:
        model = ListingGenre
        exclude = ('genre',)

    item = graphene.Field(GenreType)

    def resolve_item(self, info):
        return Genre.objects.get(id=self.genre_id)


class LanguageType(DjangoObjectType):
    class Meta:
        model = Language


class ListingLanguageType(DjangoObjectType):
    class Meta:
        model = ListingLanguage
        exclude = ('language',)

    item = graphene.Field(LanguageType)

    def resolve_item(self, info):
        return Language.objects.get(id=self.language_id)


class ListingType(DjangoObjectType):
    class Meta:
        model = Listing
        fields = ('id', 'title', 'slug', 'description', 'preview_images', 'length',)

    cover_image = graphene.Field(ImageType)
    creation_bylines = graphene.List(ListingCreationBylineType)
    collaborator_bylines = graphene.List(ListingCollaboratorBylineType)
    availability = graphene.List(ListingAvailabilityLinkType)
    additional_links = graphene.List(ListingAdditionalLinkType)
    format_set = graphene.List(ListingFormatType)
    distribution_type_set = graphene.List(ListingDistributionTypeType)
    genre_set = graphene.List(ListingGenreType)
    language_set = graphene.List(ListingLanguageType)

    def resolve_cover_image(self, info):
        listing_cover_image = ListingCoverImage.objects.get(listing_id=self.id)
        return Image.objects.get(id=listing_cover_image.image_id)

    def resolve_creation_bylines(self, info):
        return ListingCreationByline.objects.filter(listing_id=self.id)

    def resolve_collaborator_bylines(self, info):
        return ListingCollaboratorByline.objects.filter(listing_id=self.id)

    def resolve_collaborator_bylines(self, info):
        return ListingCollaboratorByline.objects.filter(listing_id=self.id)

    def resolve_availability(self, info):
        return ListingAvailabilityLink.objects.filter(listing_id=self.id)

    def resolve_additional_links(self, info):
        return ListingAdditionalLink.objects.filter(listing_id=self.id)

    def resolve_format_set(self, info):
        return ListingFormat.objects.filter(listing_id=self.id)
        # infoSet = ListingFormat.objects.filter(listing_id=self.id)
        # infoString = ''
        # for i, item in enumerate(infoSet):
        #     infoString += item.format.name
        #     if i < len(infoSet) - 1:
        #         infoString += ', '
        # return infoString

    def resolve_distribution_type_set(self, info):
        return ListingDistributionType.objects.filter(listing_id=self.id)

    def resolve_genre_set(self, info):
        return ListingGenre.objects.filter(listing_id=self.id)

    def resolve_language_set(self, info):
        return ListingLanguage.objects.filter(listing_id=self.id)


class ListingQuery(graphene.ObjectType):
    listing_bundle = graphene.List(ListingType)
    listing = graphene.Field(ListingType, id=graphene.Int(), slug=graphene.String())
    listing_creation_bylines = graphene.List(ListingCreationBylineType, user_id=graphene.Int(), listing_id=graphene.Int())

    def resolve_listing_bundle(self, info):
        return Listing.objects.all()

    def resolve_listing(self, info, **kwargs):
        id = kwargs.get('id')
        slug = kwargs.get('slug')

        if id is not None:
            return Listing.objects.get(id=id)

        if slug is not None:
            return Listing.objects.get(slug=slug)

        return None

    def resolve_listing_creation_bylines(self, info, **kwargs):
        listing_id = kwargs.get('listing_id')
        user_id = kwargs.get('user_id')

        if (user_id is not None):
            return ListingCreationByline.objects.filter(user_id=user_id)

        if (listing_id is not None):
            return ListingCreationByline.objects.filter(listing_id=listing_id)

        return None

