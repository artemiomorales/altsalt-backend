from catalog.models import *

import graphene
from graphene_django.types import DjangoObjectType
from .schema_base import CultureType
from .schema_image import ImageType


class ListingCreatorBylineType(DjangoObjectType):
    class Meta:
        model = ListingCreatorByline


class ListingCollaboratorBylineType(DjangoObjectType):
    class Meta:
        model = ListingCollaboratorByline


class ListingAvailabilityLinkType(DjangoObjectType):
    class Meta:
        model = ListingAvailabilityLink


class ListingAdditionalLinkType(DjangoObjectType):
    class Meta:
        model = ListingAdditionalLink


class PriceTypeType(DjangoObjectType):
    class Meta:
        model = PriceType


class PriceType(DjangoObjectType):
    class Meta:
        model = Price


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


class ListingCultureRepresentedType(DjangoObjectType):
    class Meta:
        model = ListingCultureRepresented
        exclude = ('culture',)

    item = graphene.Field(CultureType)

    def resolve_item(self, info):
        return Culture.objects.get(id=self.culture_id)


class ContentRatingType(DjangoObjectType):
    class Meta:
        model = ContentRating


class SeoCategoryType(DjangoObjectType):
    class Meta:
        model = SeoCategory


class ListingType(DjangoObjectType):
    class Meta:
        model = Listing
        fields = ('id', 'title', 'slug', 'description', 'preview_images', 'length', 'price', 'content_rating', 'seo_category')

    cover_image = graphene.Field(ImageType)
    creator_bylines = graphene.List(ListingCreatorBylineType)
    collaborator_bylines = graphene.List(ListingCollaboratorBylineType)
    availability = graphene.List(ListingAvailabilityLinkType)
    additional_links = graphene.List(ListingAdditionalLinkType)
    format_set = graphene.List(ListingFormatType)
    distribution_type_set = graphene.List(ListingDistributionTypeType)
    genre_set = graphene.List(ListingGenreType)
    language_set = graphene.List(ListingLanguageType)
    culture_represented = graphene.List(ListingCultureRepresentedType)
    price = graphene.Field(PriceType)
    content_rating = graphene.Field(ContentRatingType)
    seo_category = graphene.Field(SeoCategoryType)

    def resolve_cover_image(self, info):
        listing_cover_image = ListingCoverImage.objects.get(listing_id=self.id)
        return Image.objects.get(id=listing_cover_image.image_id)

    def resolve_creator_bylines(self, info):
        return ListingCreatorByline.objects.filter(listing_id=self.id)

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

    def resolve_culture_represented(self, info):
        return ListingCultureRepresented.objects.filter(listing_id=self.id)


class ListingQuery(graphene.ObjectType):
    listing_bundle = graphene.List(ListingType, approved_after_date=graphene.Date(), approved_before_date=graphene.Date())
    listing = graphene.Field(ListingType, id=graphene.Int(), slug=graphene.String())
    listing_creation_bylines = graphene.List(ListingCreatorBylineType, user_id=graphene.Int(), listing_id=graphene.Int())
    all_cultures = graphene.List(CultureType)

    def resolve_listing_bundle(self, info, **kwargs):
        approved_after_date = kwargs.get('approved_after_date')
        approved_before_date = kwargs.get('approved_before_date')

        if approved_after_date is not None:
            return Listing.objects.filter(date_approved__gte=approved_after_date, is_published=True, is_approved=True)

        if approved_before_date is not None:
            return Listing.objects.filter(date_approved__lt=approved_before_date, is_published=True, is_approved=True)

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
            return ListingCreatorByline.objects.filter(user_id=user_id)

        if (listing_id is not None):
            return ListingCreatorByline.objects.filter(listing_id=listing_id)

        return None

    def resolve_all_cultures(self, info, **kwargs):

        return Culture.objects.all()

