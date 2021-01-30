from catalog.models import *
from django.contrib.auth import get_user_model
from .schema_listing import ListingType
from .schema_user import UserType
from .schema_base import check_csrf, ImageInput, LinkInput, PriceInput, UploadInput, PriceGrapheneType, save_image_data, save_pdf_data

import graphene
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError


class SubmissionAvailabilityLinkType(DjangoObjectType):
    class Meta:
        model = SubmissionAvailabilityLink


class SubmissionAdditionalLinkType(DjangoObjectType):
    class Meta:
        model = SubmissionAdditionalLink


class SubmissionType(DjangoObjectType):
    class Meta:
        model = Submission
        fields = ('id', 'title', 'additional_info', 'date_submitted', 'is_approved')

    listing = graphene.Field(ListingType)
    creator = graphene.Field(UserType)
    file = graphene.String()
    availability = graphene.List(SubmissionAvailabilityLinkType)
    additional_links = graphene.List(SubmissionAdditionalLinkType)
    date_submitted = graphene.String()
    price = graphene.Field(PriceGrapheneType)

    def resolve_file(self, info):
        if self.file.name:
            return self.file.url
        return None

    def resolve_availability(self, info):
        return SubmissionAvailabilityLink.objects.filter(submission_id=self.id)

    def resolve_additional_links(self, info):
        return SubmissionAdditionalLink.objects.filter(submission_id=self.id)

    def resolve_date_submitted(self, info):
        return self.date_submitted.strftime("%m/%d/%y")


class CreateSubmission(graphene.Mutation):
    submission = graphene.Field(SubmissionType)

    class Arguments:
        title = graphene.String(required=True)
        cover_image = ImageInput(required=True)
        upload = UploadInput()
        availability = graphene.List(LinkInput)
        additional_links = graphene.List(LinkInput)
        price = PriceInput()
        additional_info = graphene.String()

    @classmethod
    @check_csrf
    # @login_required
    def mutate(cls, self, info, **kwargs):

        title = kwargs.get('title')
        cover_image = kwargs.get('cover_image')
        additional_info = kwargs.get('additional_info')
        availability = kwargs.get('availability')
        additional_links = kwargs.get('additional_links')
        price = kwargs.get('price')
        upload = kwargs.get('upload')

        # Create Listing
        new_listing = Listing(title=title)
        new_listing.save()
        listing_cover = ListingCoverImage(listing=new_listing)
        listing_cover.save(skip_callback=True)
        save_image_data(listing_cover, cover_image.data, cover_image.name)
        listing_cover.alttext = cover_image.alttext
        listing_cover.save(skip_callback=True)

        creator_byline = ListingCreatorByline(user=info.context.user, listing=new_listing, is_confirmed=True)
        creator_byline.save()

        # Create submission
        new_submission = Submission(title=title, date_submitted=datetime.date.today(),
                                    listing=new_listing, creator=info.context.user)
        new_submission.save()

        if additional_info is not None:
            new_submission.additional_info = additional_info

        if availability is not None:
            for link in availability:
                new_link = SubmissionAvailabilityLink(submission=new_submission, name=link.name, url=link.url,
                                                   priority=link.priority)
                new_link.save()

        if additional_links is not None:
            for link in additional_links:
                new_link = SubmissionAdditionalLink(submission=new_submission, name=link.name, url=link.url,
                                                 priority=link.priority)
                new_link.save()

        if price is not None:
            if price.price_type == 'free' or price.price_type == 'paid':
                new_price_type = PriceType.objects.get(slug=price.price_type)
                new_price = Price(price_type=new_price_type, amount=price.amount, details=price.details)
                new_price.save()
                new_submission.price = new_price

            else:
                raise GraphQLError("Price must be either free or paid")

        # Upload #
        if upload is not None:

            if upload.data != '' and upload.name != '':
                save_pdf_data(new_submission, DEFAULT_FILE_UPLOAD_NAME, upload.data, upload.name)


        return new_submission


##########
# SCHEMA #
##########


class SubmissionQuery(graphene.ObjectType):
    submission = graphene.Field(SubmissionType)
    candidate_submissions = graphene.List(SubmissionType)
    approved_submissions = graphene.Field(graphene.List(SubmissionType))

    @classmethod
    @check_csrf
    @login_required
    def resolve_submission(cls, self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Submission.objects.get(id=int(id))

        return None

    @classmethod
    @check_csrf
    @login_required
    def resolve_candidate_submissions(cls, self, info, **kwargs):
        return Submission.objects.filter(is_approved=False)

    @classmethod
    @check_csrf
    @login_required
    def resolve_approved_submissions(cls, self, info, **kwargs):
        return Submission.objects.filter(is_approved=True)






class SubmissionMutation(graphene.ObjectType):
    create_submission = CreateSubmission.Field()