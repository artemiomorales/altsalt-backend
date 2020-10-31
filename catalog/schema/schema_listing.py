from catalog.models import *
from django.contrib.auth import get_user_model

import graphene
from graphene_django.types import DjangoObjectType
from .schema_base import check_csrf, save_image_data, delete_image_data, BaseImageTypeMixin, CultureType, LinkInput, \
    NameWithPriorityInput, CultureInput, CreateCulture
from graphql_jwt.decorators import login_required
from graphql import GraphQLError


class ListingCoverImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = ListingCoverImage


class ListingPreviewImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = ListingPreviewImage


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


class PriceTypeGrapheneType(DjangoObjectType):
    class Meta:
        model = PriceType


class PriceGrapheneType(DjangoObjectType):
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


class DistributionTypeGrapheneType(DjangoObjectType):
    class Meta:
        model = DistributionType


class ListingDistributionTypeGrapheneType(DjangoObjectType):
    class Meta:
        model = ListingDistributionType
        exclude = ('distribution_type',)

    item = graphene.Field(DistributionTypeGrapheneType)

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
        fields = ('id', 'title', 'slug', 'description', 'preview_images',
                  'length', 'price', 'content_rating', 'seo_category', 'publication_date')

    cover_image = graphene.Field(ListingCoverImageType)
    preview_images = graphene.List(ListingPreviewImageType)
    creator_bylines = graphene.List(ListingCreatorBylineType)
    collaborator_bylines = graphene.List(ListingCollaboratorBylineType)
    availability = graphene.List(ListingAvailabilityLinkType)
    additional_links = graphene.List(ListingAdditionalLinkType)
    format_set = graphene.List(ListingFormatType)
    distribution_type_set = graphene.List(ListingDistributionTypeGrapheneType)
    genre_set = graphene.List(ListingGenreType)
    language_set = graphene.List(ListingLanguageType)
    culture_represented = graphene.List(ListingCultureRepresentedType)
    price = graphene.Field(PriceGrapheneType)
    content_rating = graphene.Field(ContentRatingType)
    seo_category = graphene.Field(SeoCategoryType)

    def resolve_cover_image(self, info):
        if ListingCoverImage.objects.filter(listing_id=self.id).exists():
            return ListingCoverImage.objects.get(listing_id=self.id)
        else:
            return None

    def resolve_preview_images(self, info):
        if ListingPreviewImage.objects.filter(listing_id=self.id).exists():
            return ListingPreviewImage.objects.filter(listing_id=self.id)
        else:
            return None

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


##########
# SCHEMA #
##########

class ListingQuery(graphene.ObjectType):
    listing_bundle = graphene.List(ListingType, approved_after_date=graphene.Date(), approved_before_date=graphene.Date())
    listing = graphene.Field(ListingType, id=graphene.Int(), slug=graphene.String())
    listing_creation_bylines = graphene.List(ListingCreatorBylineType, user_id=graphene.Int(), listing_id=graphene.Int())
    all_cultures = graphene.List(CultureType)
    all_distribution_types = graphene.List(DistributionTypeGrapheneType)
    all_formats = graphene.List(FormatType)
    all_lengths = graphene.List(LengthType)
    all_genres = graphene.List(GenreType)

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

    def resolve_all_formats(self, info, **kwargs):
        return Format.objects.all()

    def resolve_all_distribution_types(self, info, **kwargs):
        return DistributionType.objects.all()

    def resolve_all_genres(self, info, **kwargs):
        return Genre.objects.all()

    def resolve_all_cultures(self, info, **kwargs):
        return Culture.objects.all()


class ImageInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    data = graphene.String(required=True)
    alttext = graphene.String(required=True)


class PreviewImageInput(ImageInput):
    id = graphene.Int()
    caption = graphene.String()
    index = graphene.Int()
    delete = graphene.Boolean()


class CreateListing(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        title = graphene.String(required=True)
        slug = graphene.String(required=True)
        cover_image = ImageInput(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, title, slug, cover_image):

        new_listing = Listing(title=title, slug=slug, date_added=datetime.date.today())
        new_listing.save()

        listing_cover = ListingCoverImage(listing=new_listing)
        save_image_data(listing_cover, cover_image.data, cover_image.name)
        listing_cover.alttext = cover_image.alttext
        listing_cover.save()

        creator_byline = ListingCreatorByline(user=info.context.user, listing=new_listing)
        creator_byline.save()

        return CreateListing(listing=new_listing)


class BylineInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    priority = graphene.Int(required=True)


class PriceInput(graphene.InputObjectType):
    price_type = graphene.String(required=True)
    amount = graphene.Float()
    details = graphene.String()


class UpdateListing(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        title = graphene.String()
        slug = graphene.String(required=True)
        cover_image = ImageInput()
        description = graphene.String()
        preview_images = graphene.List(PreviewImageInput)
        availability = graphene.List(LinkInput)
        additional_links = graphene.List(LinkInput)
        publication_date = graphene.Date()
        creators = graphene.List(BylineInput)
        collaborators = graphene.List(BylineInput)
        format = graphene.List(NameWithPriorityInput)
        distribution = graphene.List(graphene.String)
        genre = graphene.List(NameWithPriorityInput)
        culture_represented = graphene.List(CultureInput)
        price = PriceInput()


    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        title = kwargs.get('title')
        slug = kwargs.get('slug')
        cover_image = kwargs.get('cover_image')
        description = kwargs.get('description')
        preview_images = kwargs.get('preview_images')
        availability = kwargs.get('availability')
        additional_links = kwargs.get('additional_links')
        publication_date = kwargs.get('publication_date')
        creators = kwargs.get('creators')
        collaborators = kwargs.get('collaborators')
        format = kwargs.get('format')
        distribution = kwargs.get('distribution')
        genre = kwargs.get('genre')
        culture_represented = kwargs.get('culture_represented')
        price = kwargs.get('price')

        if Listing.objects.filter(slug=slug).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later.")

        target_listing = Listing.objects.get(slug=slug)

        if ListingCreatorByline.objects.filter(listing=target_listing, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this listing.")

        # Title #

        if title is not None:
            target_listing.title = title

        # Slug #

        if slug is not None:
            target_listing.slug = slug

        # Description #

        if description is not None:
            target_listing.description = description

        # Cover Image #

        if cover_image is not None:

            if ListingCoverImage.objects.filter(listing=target_listing).exists() is True:
                current_cover = ListingCoverImage.objects.get(listing=target_listing)

                if cover_image.data != '':
                    delete_image_data(current_cover)
                    save_image_data(current_cover, cover_image.data, cover_image.name)

            else:
                current_cover = ListingCoverImage(listing=target_listing)

                if cover_image.data != '':
                    save_image_data(current_cover, cover_image.data, cover_image.name)

            current_cover.alttext = cover_image.alttext
            current_cover.save()

        # Preview Images #

        if preview_images is not None:

            for preview_image in preview_images:

                if preview_image.delete is True and preview_image.id is not None:

                    if ListingPreviewImage.objects.filter(listing=target_listing,
                                                          id=preview_image.id).exists() is True:
                        current_preview = ListingPreviewImage.objects.get(listing=target_listing,
                                                                          id=preview_image.id)
                        delete_image_data(current_preview)
                        current_preview.delete()

                else:
                
                    if ListingPreviewImage.objects.filter(listing=target_listing, id=preview_image.id).exists() is True:
                        current_preview = ListingPreviewImage.objects.get(listing=target_listing, id=preview_image.id)

                        if preview_image.data != '':
                            delete_image_data(current_preview)
                            save_image_data(current_preview, preview_image.data, preview_image.name)
                    else:
                        current_preview = ListingPreviewImage(listing=target_listing, index=preview_image.index)

                        if preview_image.data != '':
                            save_image_data(current_preview, preview_image.data, preview_image.name)

                    current_preview.alttext = preview_image.alttext
                    current_preview.caption = preview_image.caption
                    current_preview.save()

        # Availability #

        existing_availability = ListingAvailabilityLink.objects.filter(listing=target_listing)
        existing_availability.delete()

        if availability is not None:
            for link in availability:
                new_link = ListingAvailabilityLink(listing=target_listing, name=link.name, url=link.url,
                                                   priority=link.priority)
                new_link.save()

        # Additional Links #

        existing_additional_links = ListingAdditionalLink.objects.filter(listing=target_listing)
        existing_additional_links.delete()

        if additional_links is not None:
            for link in additional_links:
                new_link = ListingAdditionalLink(listing=target_listing, name=link.name, url=link.url,
                                                 priority=link.priority)
                new_link.save()

        # Publication Date #

        if publication_date is not None:
            target_listing.publication_date = publication_date

        # Creators #

        existing_creators = ListingCreatorByline.objects.filter(listing=target_listing)
        existing_creators.delete()

        if creators is not None:
            for creator in creators:
                if get_user_model().objects.filter(username=creator.username).exists():
                    stored_user = get_user_model().objects.get(username=creator.username)
                    creator_byline = ListingCreatorByline(user=stored_user, listing=target_listing,
                                                          listing_priority=creator.priority)
                    creator_byline.save()
                else:
                    raise GraphQLError('Specified user {0} does not exist'.format(creator.username))

        # Collaborators #

        existing_collaborators = ListingCollaboratorByline.objects.filter(listing=target_listing)
        existing_collaborators.delete()

        if collaborators is not None:
            for collaborator in collaborators:
                if get_user_model().objects.filter(username=collaborator.username).exists():
                    stored_user = get_user_model().objects.get(username=collaborator.username)
                    collaborator_byline = ListingCollaboratorByline(user=stored_user, listing=target_listing,
                                                          listing_priority=collaborator.priority)
                    collaborator_byline.save()
                else:
                    raise GraphQLError('Specified user {0} does not exist'.format(creator.username))

        # Price #

        if getattr(target_listing, "price") is not None:
            target_listing.price.delete()

        if price is not None:

            if price.price_type == 'free' or price.price_type == 'paid':
                new_price_type = PriceType.objects.get(slug=price.price_type)
                new_price = Price(price_type=new_price_type, amount=price.amount, details=price.details)
                new_price.save()
                target_listing.price = new_price

            else:
                raise GraphQLError("Price must be either free or paid")

        # Format #

        existing_format = ListingFormat.objects.filter(listing=target_listing)
        existing_format.delete()

        if format is not None:
            for item in format:
                item_slug = slugify(item.name)
                if Format.objects.filter(slug=item_slug).exists() is False:
                    new_model = Format(name=item.name, slug=item_slug)
                    new_model.save()

                item_object = Format.objects.get(slug=item_slug)
                new_item_record = ListingFormat(listing=target_listing, format=item_object,
                                                priority=item.priority)
                new_item_record.save()

        # Distribution #

        existing_distribution = ListingDistributionType.objects.filter(listing=target_listing)
        existing_distribution.delete()

        if distribution is not None:
            for item in distribution:
                if DistributionType.objects.filter(slug=item).exists() is False:
                    raise GraphQLError("Attempted to save Invalid distribution type")

                item_object = DistributionType.objects.get(slug=item)
                new_item_record = ListingDistributionType(listing=target_listing, distribution_type=item_object)
                new_item_record.save()

        # Genre #

        existing_genre = ListingGenre.objects.filter(listing=target_listing)
        existing_genre.delete()

        if genre is not None:
            for item in genre:
                item_slug = slugify(item.name)
                if Genre.objects.filter(slug=item_slug).exists() is False:
                    new_model = Genre(name=item.name, slug=item_slug)
                    new_model.save()

                item_object = Genre.objects.get(slug=item_slug)
                new_item_record = ListingGenre(listing=target_listing, genre=item_object,
                                               priority=item.priority)
                new_item_record.save()

        # Culture Represented #

        existing_culture_represented = ListingCultureRepresented.objects.filter(listing=target_listing)
        existing_culture_represented.delete()

        if culture_represented is not None:
            for item in culture_represented:
                item_slug = slugify(item.name)
                if Culture.objects.filter(slug=item_slug).exists() is False:
                    CreateCulture(item.name, item_slug, item.continent)

                item_object = Culture.objects.get(slug=item_slug)
                new_item_record = ListingCultureRepresented(listing=target_listing, culture=item_object, priority=item.priority)
                new_item_record.save()

        target_listing.save()
        return UpdateListing(listing=target_listing)



class ListingMutation(graphene.ObjectType):
    create_listing = CreateListing.Field()
    update_listing = UpdateListing.Field()
