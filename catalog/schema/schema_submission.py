from catalog.models import *
from catalog.models.base import PriceType
from django.contrib.auth import get_user_model
from .schema_listing import ListingType
from .schema_base import check_csrf, ImageInput, LinkInput, PriceInput, UploadInput,\
    PriceGrapheneType, save_image_data_via_model, save_pdf_data, create_presigned_url, send_submission_approved_email, \
    send_submission_rejected_email, send_moderator_notification_email

import graphene
from graphene_django.types import DjangoObjectType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError
import datetime

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
    creator = graphene.Field('catalog.schema.schema_user.UserType')
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
    @login_required
    def mutate(cls, self, info, **kwargs):

        title = kwargs.get('title')
        cover_image = kwargs.get('cover_image')
        additional_info = kwargs.get('additional_info')
        availability = kwargs.get('availability')
        additional_links = kwargs.get('additional_links')
        price = kwargs.get('price')
        upload = kwargs.get('upload')

        # Create Listing
        new_listing = Listing(title=title, is_editable=False)
        new_listing.save()
        listing_cover = ListingCoverImage(listing=new_listing)
        listing_cover.save(skip_callback=True)
        save_image_data_via_model(listing_cover, cover_image.data, cover_image.name)
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
                new_submission.save()

            else:
                raise GraphQLError("Price must be either free or paid")

        # Upload #
        if upload is not None:

            if upload.data != '' and upload.name != '':
                save_pdf_data(new_submission, DEFAULT_FILE_UPLOAD_NAME, upload.data, upload.name)

        moderators = get_user_model().objects.filter(is_moderator=True)
        for moderator in moderators:
            send_moderator_notification_email(moderator.email, new_submission.title)

        return new_submission


class GetSubmissionDownloadLink(graphene.Mutation):
     download_link = graphene.String()

     class Arguments:
         id = graphene.String(required=True)

     @classmethod
     @check_csrf
     @login_required
     def mutate(cls, self, info, **kwargs):

        if info.context.user.is_moderator is False:
            raise GraphQLError("You are not authorized to download this file.")

        id = kwargs.get('id')

        if Submission.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target submission does not exist! Please refresh or try again later.")

        submission = Submission.objects.get(id=int(id))
        if submission.file.name:
            return GetSubmissionDownloadLink(download_link=create_presigned_url(submission.file.name))

        raise GraphQLError("Target submission has no associated file!")


class ApproveSubmission(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.String(required=True)
        message = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        if info.context.user.is_moderator is False:
            raise GraphQLError("You are not authorized to perform this action.")

        id = kwargs.get('id')
        message = kwargs.get('message')

        if Submission.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target submission does not exist! Please refresh or try again later.")

        submission = Submission.objects.get(id=id)
        if submission.listing is None:
            raise GraphQLError("Error - related listing not found!")

        submission.is_approved = True
        submission.save()

        # Migrate values to listing
        listing = submission.listing

        # Price
        new_price_type = PriceType.objects.get(slug=submission.price.price_type.slug)
        new_price = Price(price_type=new_price_type, amount=submission.price.amount, details=submission.price.details)
        new_price.save()
        listing.price = new_price
        listing.price = submission.price

        if SubmissionAvailabilityLink.objects.filter(submission=submission).exists() is True:
            submission_availability = SubmissionAvailabilityLink.objects.filter(submission=submission)
            for link in submission_availability:
                new_link = ListingAvailabilityLink(listing=listing, name=link.name, url=link.url,
                                                   priority=link.priority)
                new_link.save()

        if SubmissionAdditionalLink.objects.filter(submission=submission).exists() is True:
            submission_additional_links = SubmissionAdditionalLink.objects.filter(submission=submission)
            for link in submission_additional_links:
                new_link = ListingAdditionalLink(listing=listing, name=link.name, url=link.url,
                                                 priority=link.priority)
                new_link.save()

        listing.save()
        send_submission_approved_email(target_username=submission.creator.username,
                                       submission_title=submission.title,
                                       target_email=submission.creator.email,
                                       message=message)

        return ApproveSubmission(success=True)


class ConfirmSubmissionApproval(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        id = kwargs.get('id')

        if Submission.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target submission does not exist! Please refresh or try again later.")

        submission = Submission.objects.get(id=id)

        if submission.creator.username != info.context.user.username:
            raise GraphQLError("You are not authorized to perform this action.")

        if submission.listing is not None:
            listing = submission.listing
            listing.is_editable = True
            listing.save()
            return ConfirmSubmissionApproval(success=True)

        raise GraphQLError("Target listing does not exist! Please refresh or try again later.")


class DeleteSubmission(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        id = graphene.String(required=True)
        message = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        if info.context.user.is_moderator is False:
            raise GraphQLError("You are not authorized to perform this action.")

        id = kwargs.get('id')
        message = kwargs.get('message')

        if Submission.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target submission does not exist! Please refresh or try again later.")

        submission = Submission.objects.get(id=id)

        send_submission_rejected_email(target_username=submission.creator.username,
                                       submission_title=submission.title,
                                       target_email=submission.creator.email,
                                       message=message)

        if submission.listing is not None:
            listing = submission.listing
            listing.delete()

        submission.delete()
        return DeleteSubmission(success=True)


class SubmissionMutation(graphene.ObjectType):
    create_submission = CreateSubmission.Field()
    get_submission_download_link = GetSubmissionDownloadLink.Field()
    approve_submission = ApproveSubmission.Field()
    confirm_submission_approval = ConfirmSubmissionApproval.Field()
    delete_submission = DeleteSubmission.Field()