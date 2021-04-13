from catalog.models import *
from django.contrib.auth import get_user_model

import graphene
from graphene_django.types import DjangoObjectType
from .schema_base import check_csrf, save_image_data, BaseImageTypeMixin, CountryType, IdentityType, LinkInput, \
    NameWithPriorityInput, UserInput, send_byline_email, save_pdf_data, ImageInput, PriceInput, ThreadType, \
    UploadInput, PriceGrapheneType, send_listing_public_email, TagType, FormatType, \
    GenreType, DistributionTypeGrapheneType, LengthType, LanguageType, ContentRatingType, SeoCategoryType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError

import datetime

from catalog.constants import get_date_from_string, capitalize_string, DEFAULT_FILE_UPLOAD_NAME
from django.utils import timezone


class ListingUploadType(DjangoObjectType):
    file = graphene.String()

    def resolve_file(self, info):
        if self.file.name:
            return self.file.url
        return None

    class Meta:
        model = ListingUpload


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


class ListingFormatType(DjangoObjectType):
    class Meta:
        model = ListingFormat
        exclude = ('format',)

    item = graphene.Field(FormatType)

    def resolve_item(self, info):
        return Format.objects.get(id=self.format_id)


class ListingTagType(DjangoObjectType):
    class Meta:
        model = ListingTag
        exclude = ('tag',)

    item = graphene.Field(TagType)

    def resolve_item(self, info):
        return Tag.objects.get(id=self.tag_id)


class ListingDistributionTypeGrapheneType(DjangoObjectType):
    class Meta:
        model = ListingDistributionType
        exclude = ('distribution_type',)

    item = graphene.Field(DistributionTypeGrapheneType)

    def resolve_item(self, info):
        return DistributionType.objects.get(id=self.distribution_type_id)


class ListingGenreType(DjangoObjectType):
    class Meta:
        model = ListingGenre
        exclude = ('genre',)

    item = graphene.Field(GenreType)

    def resolve_item(self, info):
        return Genre.objects.get(id=self.genre_id)


class ListingLanguageType(DjangoObjectType):
    class Meta:
        model = ListingLanguage
        exclude = ('language',)

    item = graphene.Field(LanguageType)

    def resolve_item(self, info):
        return Language.objects.get(id=self.language_id)


class ListingCountryRepresentedType(DjangoObjectType):
    class Meta:
        model = ListingCountryRepresented
        exclude = ('country',)

    item = graphene.Field(CountryType)

    def resolve_item(self, info):
        return Country.objects.get(id=self.country_id)


class ListingIdentityRepresentedType(DjangoObjectType):
    class Meta:
        model = ListingIdentityRepresented
        exclude = ('identity',)

    item = graphene.Field(IdentityType)

    def resolve_item(self, info):
        return Identity.objects.get(id=self.identity_id)


class ListingThreadType(DjangoObjectType):
    class Meta:
        model = ListingThread
        exclude = ('thread',)

    item = graphene.Field(ThreadType)

    def resolve_item(self, info):
        return Thread.objects.get(id=self.thread_id)


class ListingType(DjangoObjectType):
    class Meta:
        model = Listing
        fields = ('id', 'title', 'short_name', 'description', 'preview_images',
                  'length', 'price', 'content_rating', 'seo_category',
                  'is_published', 'is_approved', 'publication_date', 'date_added', 'is_editable',
                  'show_custom_author', 'custom_author', 'is_html')

    slug = graphene.String()
    cover_image = graphene.Field(ListingCoverImageType)
    preview_images = graphene.List(ListingPreviewImageType)
    creator_bylines = graphene.List(ListingCreatorBylineType)
    collaborator_bylines = graphene.List(ListingCollaboratorBylineType)
    upload = graphene.Field(ListingUploadType)
    availability = graphene.List(ListingAvailabilityLinkType)
    additional_links = graphene.List(ListingAdditionalLinkType)
    format_set = graphene.List(ListingFormatType)
    distribution_type_set = graphene.List(ListingDistributionTypeGrapheneType)
    genre_set = graphene.List(ListingGenreType)
    language_set = graphene.List(ListingLanguageType)
    countries_represented = graphene.List(ListingCountryRepresentedType)
    identities_represented = graphene.List(ListingIdentityRepresentedType)
    tag_set = graphene.List(ListingTagType)
    price = graphene.Field(PriceGrapheneType)
    content_rating = graphene.Field(ContentRatingType)
    seo_category = graphene.Field(SeoCategoryType)
    date_added = graphene.String()
    submission_approved = graphene.Boolean()
    moderator_authentication = graphene.Boolean()
    thread_set = graphene.List(ListingThreadType)

    def resolve_slug(self, info):
        return slugify(self.title)

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

    def resolve_upload(self, info):
        if ListingUpload.objects.filter(listing_id=self.id).exists():
            return ListingUpload.objects.get(listing_id=self.id)
        else:
            return None

    def resolve_availability(self, info):
        return ListingAvailabilityLink.objects.filter(listing_id=self.id)

    def resolve_additional_links(self, info):
        return ListingAdditionalLink.objects.filter(listing_id=self.id)

    def resolve_format_set(self, info):
        return ListingFormat.objects.filter(listing_id=self.id)

    def resolve_distribution_type_set(self, info):
        return ListingDistributionType.objects.filter(listing_id=self.id)

    def resolve_genre_set(self, info):
        return ListingGenre.objects.filter(listing_id=self.id)

    def resolve_language_set(self, info):
        return ListingLanguage.objects.filter(listing_id=self.id)

    def resolve_countries_represented(self, info):
        return ListingCountryRepresented.objects.filter(listing_id=self.id)

    def resolve_identities_represented(self, info):
        return ListingIdentityRepresented.objects.filter(listing_id=self.id)

    def resolve_tag_set(self, info):
        return ListingTag.objects.filter(listing_id=self.id)

    def resolve_date_added(self, info):
        return self.date_added.strftime("%m/%d/%y")

    def resolve_submission_approved(self, info):
        if Submission.objects.filter(listing_id=self.id).exists():
            submission = Submission.objects.get(listing_id=self.id)
            return submission.is_approved
        return True

    def resolve_moderator_authentication(self, info):
        if info.context.user.is_authenticated is True and info.context.user.is_moderator is True:
            return True
        return False

    def resolve_thread_set(self, info):
        return ListingThread.objects.filter(listing_id=self.id)


##########
# SCHEMA #
##########

class ListingQuery(graphene.ObjectType):
    featured_listings = graphene.List(ListingType)
    candidate_listings = graphene.List(ListingType)
    listing_bundle = graphene.List(ListingType,
                                   include_featured=graphene.Boolean(default_value=True),
                                   exclude_private=graphene.Boolean(default_value=True),
                                   approved_after_date=graphene.Date(),
                                   approved_before_date=graphene.Date()
                                   )
    listing = graphene.Field(ListingType, id=graphene.String())
    listing_creation_bylines = graphene.List(ListingCreatorBylineType, user_id=graphene.Int(), listing_id=graphene.Int())
    all_content_ratings = graphene.List(ContentRatingType)
    all_languages = graphene.List(LanguageType)
    all_countries = graphene.List(CountryType)
    all_identities = graphene.List(IdentityType)
    all_distribution_types = graphene.List(DistributionTypeGrapheneType)
    all_lengths = graphene.List(LengthType)
    all_formats = graphene.List(FormatType)
    all_lengths = graphene.List(LengthType)
    all_genres = graphene.List(GenreType)
    all_tags = graphene.List(TagType)

    def resolve_featured_listings(self, info, **kwargs):
        return Listing.objects.filter(is_featured=True)

    def resolve_candidate_listings(self, info, **kwargs):
        return Listing.objects.filter(is_approved=False, is_published=True)

    def resolve_listing_bundle(self, info, **kwargs):
        include_featured = kwargs.get('include_featured')
        exclude_private = kwargs.get('exclude_private')
        approved_after_date = kwargs.get('approved_after_date')
        approved_before_date = kwargs.get('approved_before_date')

        if include_featured is True:
            listings = Listing.objects.all()
        else:
            listings = Listing.objects.filter(is_featured=False)

        if exclude_private is True:
            listings = listings.filter(is_published=True, is_approved=True)

        if approved_after_date is not None:
            listings = listings.filter(date_approved__gte=approved_after_date)

        if approved_before_date is not None:
            listings = listings.filter(date_approved__lt=approved_before_date)

        return listings

    def resolve_listing(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Listing.objects.get(id=int(id))

        return None

    def resolve_listing_creation_bylines(self, info, **kwargs):
        listing_id = kwargs.get('listing_id')
        user_id = kwargs.get('user_id')

        if (user_id is not None):
            return ListingCreatorByline.objects.filter(user_id=user_id)

        if (listing_id is not None):
            return ListingCreatorByline.objects.filter(listing_id=listing_id)

        return None

    def resolve_all_content_ratings(self, info, **kwargs):
        return ContentRating.objects.all()

    def resolve_all_languages(self, info, **kwargs):
        return Language.objects.all()

    def resolve_all_formats(self, info, **kwargs):
        return Format.objects.all()

    def resolve_all_distribution_types(self, info, **kwargs):
        return DistributionType.objects.all()

    def resolve_all_lengths(self, info, **kwargs):
        return Length.objects.all()

    def resolve_all_genres(self, info, **kwargs):
        return Genre.objects.all()

    def resolve_all_countries(self, info, **kwargs):
        return Country.objects.all()

    def resolve_all_identities(self, info, **kwargs):
        return Identity.objects.all()

    def resolve_all_tags(self, info, **kwargs):
        return Tag.objects.all()


class PreviewImageInput(ImageInput):
    id = graphene.Int()
    caption = graphene.String()
    index = graphene.Int()
    delete = graphene.Boolean()


class CreateListing(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        title = graphene.String(required=True)
        cover_image = ImageInput(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, title, cover_image):

        # Disabled for now

        if info.context.user.is_verified is False and info.context.user.is_moderator is False:
            raise GraphQLError("You are not authorized to perform this action")

        new_listing = Listing(title=title, date_added=datetime.date.today())
        new_listing.save()

        listing_cover = ListingCoverImage(listing=new_listing)
        listing_cover.save(skip_callback=True)
        save_image_data(listing_cover, cover_image.data, cover_image.name)
        listing_cover.alttext = cover_image.alttext
        listing_cover.save(skip_callback=True)

        creator_byline = ListingCreatorByline(user=info.context.user, listing=new_listing, is_confirmed=True)
        creator_byline.save()

        return CreateListing(listing=new_listing)


class UpdateListing(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        id = graphene.String(required=True)
        title = graphene.String()
        short_name = graphene.String()
        description = graphene.String()
        is_published = graphene.Boolean()
        cover_image = ImageInput()
        preview_images = graphene.List(PreviewImageInput)
        upload = UploadInput()
        availability = graphene.List(LinkInput)
        additional_links = graphene.List(LinkInput)
        publication_date = graphene.String()
        creators = graphene.List(UserInput)
        collaborators = graphene.List(UserInput)
        show_custom_author = graphene.Boolean()
        custom_author = graphene.String()
        content_rating = graphene.String()
        length = graphene.String()
        language = graphene.List(NameWithPriorityInput)
        format = graphene.List(NameWithPriorityInput)
        distribution = graphene.List(graphene.String)
        genre = graphene.List(NameWithPriorityInput)
        countries_represented = graphene.List(NameWithPriorityInput)
        identities_represented = graphene.List(NameWithPriorityInput)
        tag = graphene.List(NameWithPriorityInput)
        price = PriceInput()


    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        id = kwargs.get('id')
        title = kwargs.get('title')
        short_name = kwargs.get('short_name')
        is_published = kwargs.get('is_published')
        cover_image = kwargs.get('cover_image')
        description = kwargs.get('description')
        preview_images = kwargs.get('preview_images')
        upload = kwargs.get('upload')
        availability = kwargs.get('availability')
        additional_links = kwargs.get('additional_links')
        publication_date = kwargs.get('publication_date')
        creators = kwargs.get('creators')
        collaborators = kwargs.get('collaborators')
        show_custom_author = kwargs.get('show_custom_author')
        custom_author = kwargs.get('custom_author')
        content_rating = kwargs.get('content_rating')
        length = kwargs.get('length')
        language = kwargs.get('language')
        format = kwargs.get('format')
        distribution = kwargs.get('distribution')
        genre = kwargs.get('genre')
        countries_represented = kwargs.get('countries_represented')
        identities_represented = kwargs.get('identities_represented')
        tag = kwargs.get('tag')
        price = kwargs.get('price')

        if Listing.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later.")

        target_listing = Listing.objects.get(id=id)

        if ListingCreatorByline.objects.filter(listing=target_listing, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this listing.")

        # Title #

        if title is not None:
            target_listing.title = title

        # Short name #

        if short_name is not None:
            target_listing.short_name = short_name

        # Description #

        if description is not None:
            target_listing.description = description

        # Is Published #

        if is_published is not None:
            target_listing.is_published = is_published

        # Cover Image #

        if cover_image is not None:

            if ListingCoverImage.objects.filter(listing=target_listing).exists() is True:
                current_cover = ListingCoverImage.objects.get(listing=target_listing)

            else:
                current_cover = ListingCoverImage(listing=target_listing)
                current_cover.save(skip_callback=True)

            if cover_image.data != '':
                save_image_data(current_cover, cover_image.data, cover_image.name)

            current_cover.alttext = cover_image.alttext
            current_cover.save(skip_callback=True)

        # Preview Images #

        if preview_images is not None:

            for preview_image in preview_images:

                if preview_image.delete is True and preview_image.id is not None:

                    if ListingPreviewImage.objects.filter(listing=target_listing,
                                                          id=preview_image.id).exists() is True:
                        current_preview = ListingPreviewImage.objects.get(listing=target_listing,
                                                                          id=preview_image.id)
                        current_preview.delete()

                else:
                
                    if ListingPreviewImage.objects.filter(listing=target_listing, id=preview_image.id).exists() is True:
                        current_preview = ListingPreviewImage.objects.get(listing=target_listing, id=preview_image.id)

                    else:
                        current_preview = ListingPreviewImage(listing=target_listing, index=preview_image.index)
                        current_preview.save(skip_callback=True)

                    if preview_image.data != '':
                        save_image_data(current_preview, preview_image.data, preview_image.name)

                    current_preview.alttext = preview_image.alttext
                    current_preview.caption = preview_image.caption
                    current_preview.save(skip_callback=True)

        # Upload #

        if upload is not None:

            if upload.delete is True:

                if ListingUpload.objects.filter(listing=target_listing).exists() is True:
                    current_upload = ListingUpload.objects.get(listing=target_listing)
                    current_upload.delete()

            else:

                if ListingUpload.objects.filter(listing=target_listing).exists() is True:
                    current_upload = ListingUpload.objects.get(listing=target_listing)

                else:
                    current_upload = ListingUpload(listing=target_listing, is_preview=False, allow_downloads=False)
                    current_upload.save()

                current_upload.allow_downloads = upload.allow_downloads
                current_upload.is_preview = upload.is_preview
                current_upload.save()

                if upload.data != '' and upload.name != '':
                    save_pdf_data(current_upload, DEFAULT_FILE_UPLOAD_NAME, upload.data, upload.name)


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
            if publication_date == '':
                target_listing.publication_date = None
            else:
                target_listing.publication_date = get_date_from_string(publication_date + '01')

        # Creators #

        if creators is not None:

            creator_input_valid = False

            for creator in creators:
                if get_user_model().objects.filter(username=creator.username).exists():
                    creator_input_valid = True

            if creator_input_valid:
                existing_creator_bylines = ListingCreatorByline.objects.filter(listing=target_listing)

                for existing_creator_byline in existing_creator_bylines:
                    delete_existing_byline = True
                    for creator in creators:
                        if get_user_model().objects.filter(username=creator.username).exists() and \
                           existing_creator_byline.user.username == creator.username:
                            delete_existing_byline = False
                    if delete_existing_byline:
                        existing_creator_byline.delete()

                for creator in creators:
                    if get_user_model().objects.filter(username=creator.username).exists():
                        stored_user = get_user_model().objects.get(username=creator.username)
                        if ListingCreatorByline.objects.filter(listing=target_listing, user=stored_user).exists():
                            creator_byline = ListingCreatorByline.objects.get(listing=target_listing, user=stored_user)
                            creator_byline.listing_priority = creator.priority
                        else:
                            creator_byline = ListingCreatorByline(user=stored_user, listing=target_listing,
                                                                  listing_priority=creator.priority, requester=info.context.user)
                            send_byline_email(info.context.user.display_name, target_listing.title, stored_user.email,
                                              'creator')
                        creator_byline.save()
                    else:
                        raise GraphQLError('Specified user {0} does not exist. Please remove and try again.'.format(creator.username))
            else:
                raise GraphQLError('Unable to process request. Listing must contain at least one valid creator.'
                                   ' Please refresh and try again.')

        # Collaborators #

        if collaborators is not None:

            existing_collaborator_bylines = ListingCollaboratorByline.objects.filter(listing=target_listing)

            for existing_collaborator_byline in existing_collaborator_bylines:
                delete_existing_byline = True
                for collaborator in collaborators:
                    if get_user_model().objects.filter(username=collaborator.username).exists() and \
                       existing_collaborator_byline.user.username == collaborator.username:
                        delete_existing_byline = False
                if delete_existing_byline:
                    existing_collaborator_byline.delete()

            for collaborator in collaborators:
                if get_user_model().objects.filter(username=collaborator.username).exists():
                    stored_user = get_user_model().objects.get(username=collaborator.username)
                    if ListingCollaboratorByline.objects.filter(listing=target_listing, user=stored_user).exists():
                        collaborator_byline = ListingCollaboratorByline.objects.get(listing=target_listing, user=stored_user)
                        collaborator_byline.listing_priority = collaborator.priority
                    else:
                        collaborator_byline = ListingCollaboratorByline(user=stored_user, listing=target_listing,
                                                              listing_priority=collaborator.priority, requester=info.context.user)
                        send_byline_email(info.context.user.display_name, target_listing.title, stored_user.email,
                                                'collaborator')
                    collaborator_byline.save()
                else:
                    raise GraphQLError('Specified user {0} does not exist. Please remove and try again'.format(collaborator.username))

        # Custom Author #

        if show_custom_author is not None:
            target_listing.show_custom_author = show_custom_author

        if custom_author is not None:
            target_listing.custom_author = custom_author


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

        # Content Rating #

        if content_rating is not None:

            if ContentRating.objects.filter(slug=content_rating).exists() is False:
                raise GraphQLError("Invalid content rating")

            item_object = ContentRating.objects.get(slug=content_rating)
            target_listing.content_rating = item_object

        # Length #

        if length is not None:

            if Length.objects.filter(slug=length).exists() is False:
                raise GraphQLError("Invalid length")

            item_object = Length.objects.get(slug=length)
            target_listing.length = item_object

        # Language #

        existing_language = ListingLanguage.objects.filter(listing=target_listing)
        existing_language.delete()

        if language is not None:
            for item in language:
                item_slug = slugify(item.name)
                if Language.objects.filter(slug=item_slug).exists() is False:
                    new_model = Language(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Language.objects.get(slug=item_slug)
                new_item_record = ListingLanguage(listing=target_listing, language=item_object,
                                                  priority=item.priority)
                new_item_record.save()

        # Format #

        existing_format = ListingFormat.objects.filter(listing=target_listing)
        existing_format.delete()

        if format is not None:
            for item in format:
                item_slug = slugify(item.name)
                if Format.objects.filter(slug=item_slug).exists() is False:
                    new_model = Format(name=capitalize_string(item.name), slug=item_slug)
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
                    new_model = Genre(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Genre.objects.get(slug=item_slug)
                new_item_record = ListingGenre(listing=target_listing, genre=item_object,
                                               priority=item.priority)
                new_item_record.save()

        # Countries Represented #

        existing_countries_represented = ListingCountryRepresented.objects.filter(listing=target_listing)
        existing_countries_represented.delete()

        if countries_represented is not None:
            for item in countries_represented:
                item_slug = slugify(item.name)
                if Country.objects.filter(slug=item_slug).exists() is False:
                    new_country = Country(name=item.name.capitalize(), slug=item_slug)
                    new_country.save()

                item_object = Country.objects.get(slug=item_slug)
                new_item_record = ListingCountryRepresented(listing=target_listing, country=item_object, priority=item.priority)
                new_item_record.save()

        # Identities Represented #

        existing_identities_represented = ListingIdentityRepresented.objects.filter(listing=target_listing)
        existing_identities_represented.delete()

        if identities_represented is not None:
            for item in identities_represented:
                item_slug = slugify(item.name)
                if Identity.objects.filter(slug=item_slug).exists() is False:
                    new_identity = Identity(name=capitalize_string(item.name), slug=item_slug)
                    new_identity.save()

                item_object = Identity.objects.get(slug=item_slug)
                new_item_record = ListingIdentityRepresented(listing=target_listing, identity=item_object, priority=item.priority)
                new_item_record.save()

        # Tag #

        existing_tag = ListingTag.objects.filter(listing=target_listing)
        existing_tag.delete()

        if tag is not None:
            for item in tag:
                item_slug = slugify(item.name)
                if Tag.objects.filter(slug=item_slug).exists() is False:
                    new_model = Tag(name=capitalize_string(item.name), slug=item_slug)
                    new_model.save()

                item_object = Tag.objects.get(slug=item_slug)
                new_item_record = ListingTag(listing=target_listing, tag=item_object,
                                                priority=item.priority)
                new_item_record.save()

        target_listing.save()
        return UpdateListing(listing=target_listing)


class UpdateListingApproval(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        id = graphene.String(required=True)
        target_status = graphene.Boolean(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, id, target_status):

        if info.context.user.is_moderator is False:
            raise GraphQLError("You are not authorized to perform this action.")

        target_listing = Listing.objects.get(id=id)

        # Only send confirmation email if the status has changed to true

        status_changed = False

        if target_listing.is_approved is not target_status:
            status_changed = True

        if status_changed is True and target_status is True:
            target_listing.date_approved = timezone.now()
            creator_bylines = ListingCreatorByline.objects.filter(listing=target_listing)
            for creator_byline in creator_bylines:
                send_listing_public_email(target_username=creator_byline.user.username,
                                          listing_title=target_listing.title,
                                          target_email=creator_byline.user.email)

        target_listing.is_approved = target_status
        target_listing.save()

        return UpdateListingApproval(listing=target_listing)


class DeleteListing(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, id):

        if Listing.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later.")

        target_listing = Listing.objects.get(id=id)

        if ListingCreatorByline.objects.filter(listing=target_listing, user=info.context.user).exists() is False:
            raise GraphQLError("You are not authorized to update this listing.")

        if Submission.objects.filter(listing_id=id):
            related_submission = Submission.objects.get(listing_id=id)
            related_submission.delete()

        target_listing.delete()
        return True


class CreateListingThread(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        listing = graphene.String(required=True)
        body = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        listing = kwargs.get('listing')
        body = kwargs.get('body')

        if Listing.objects.filter(id=listing).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later.")

        target_listing = Listing.objects.get(id=listing)

        # if ListingThread.objects.filter(listing=target_listing).exists():
        #     listing_threads = ListingThread.objects.filter(listing=target_listing)
        #     for listing_thread in listing_threads:
        #         if listing_thread.thread.originator == info.context.user:
        #             raise GraphQLError("You've already resonated on this listing")

        if body.strip() == '':
            raise GraphQLError("Comment body must not be empty")

        new_thread = Thread(originator=info.context.user)
        new_thread.save()

        new_listing_thread = ListingThread(listing=target_listing, thread=new_thread)
        new_listing_thread.save()

        new_comment = Comment(thread=new_thread, commenter=info.context.user, body=body, is_root=True)
        new_comment.save()

        # Create notifications

        creator_bylines = ListingCreatorByline.objects.filter(listing=target_listing)
        for creator_byline in creator_bylines:
            if info.context.user != creator_byline.user:
                notification = Notification(content_object=new_listing_thread, notifier=info.context.user,
                                            recipient=creator_byline.user)
                notification.save()

        collaborator_bylines = ListingCollaboratorByline.objects.filter(listing=target_listing)
        for collaborator_byline in collaborator_bylines:
            if info.context.user != collaborator_byline.user:
                notification = Notification(content_object=new_listing_thread, notifier=info.context.user,
                                            recipient=collaborator_byline.user)
                notification.save()

        return CreateListingThread(listing=target_listing)


class CreateListingThreadReply(graphene.Mutation):
    listing = graphene.Field(ListingType)

    class Arguments:
        listing = graphene.String(required=True)
        thread = graphene.String(required=True)
        body = graphene.String()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        listing = kwargs.get('listing')
        thread = kwargs.get('thread')
        body = kwargs.get('body')

        if Listing.objects.filter(id=listing).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later")

        if Thread.objects.filter(id=thread).exists() is False:
            raise GraphQLError("Target thread does not exist! Please refresh or try again later")

        target_listing = Listing.objects.get(id=listing)
        target_thread = Thread.objects.get(id=thread)

        can_reply = False

        if target_thread.originator == info.context.user:
            can_reply = True

        if can_reply is False:
            creator_bylines = ListingCreatorByline.objects.filter(listing=target_listing)
            for creator_byline in creator_bylines:
                if creator_byline.user == info.context.user:
                    can_reply = True
                    break

        if can_reply is False:
            collaborator_bylines = ListingCollaboratorByline.objects.filter(listing=target_listing)
            for collaborator_byline in collaborator_bylines:
                if collaborator_byline.user == info.context.user:
                    can_reply = True
                    break

        if can_reply is False:
            raise GraphQLError("Only original posters, creators, and collaborators may reply to threads")

        if body.strip() == '':
            raise GraphQLError("Comment body must not be empty")

        new_comment = Comment(thread=target_thread, commenter=info.context.user, body=body, is_root=False)
        new_comment.save()

        # Create notifications
        thread_comments = Comment.objects.filter(thread=target_thread)
        thread_subscribers = []
        for thread_comment in thread_comments:
            if info.context.user != thread_comment.commenter and thread_comment.commenter not in thread_subscribers:
                thread_subscribers.append(thread_comment.commenter)

        for subscriber in thread_subscribers:
            notification = Notification(content_object=new_comment, notifier=info.context.user,
                                        recipient=subscriber)
            notification.save()

        return CreateListingThreadReply(listing=target_listing)


class ListingMutation(graphene.ObjectType):
    create_listing = CreateListing.Field()
    update_listing = UpdateListing.Field()
    delete_listing = DeleteListing.Field()
    update_listing_approval = UpdateListingApproval.Field()
    create_listing_thread = CreateListingThread.Field()
    create_listing_thread_reply = CreateListingThreadReply.Field()