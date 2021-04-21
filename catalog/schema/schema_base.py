import graphene
from catalog.models.base import Country, Identity, Thread, Comment, ReactionType, CommentReaction, Notification, Tag, \
    Format, Genre, DistributionType, Length, Language, ContentRating, SeoCategory, ContentThread
from catalog.models.base import Price
from catalog.models.user import NotificationSettings, NotificationSettingsAuthorizedUpdate
from catalog.utils import GenerateRandomString
from django.contrib.auth.hashers import make_password
from graphene_django.types import DjangoObjectType, ObjectType
from django.conf import settings
from django.middleware.csrf import _sanitize_token, _compare_salted_tokens
from graphql import GraphQLError
from graphene.types import Scalar

import os
import base64
import PIL.Image as ImageUtils
from django.core.files.base import ContentFile
from django.core.files.uploadhandler import InMemoryUploadedFile
from io import BytesIO
from django.utils import timezone
from django.template.defaultfilters import slugify

from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, get_image_buffer
from botocore.exceptions import ClientError
import boto3
from botocore.config import Config

# JWT
from graphql_jwt.decorators import login_required


# Email

import logging
import sendgrid
from sendgrid.helpers.mail import *


# Rate limiting

from ratelimit.core import is_ratelimited


# Storage
from catalog.backends import CatalogImageStorage


from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


def check_csrf(f):

    def wrapper(cls, self, info, **kwargs):
        if settings.CSRF_COOKIE_NAME in info.context.COOKIES and \
                'X-Csrftoken' in info.context.headers:

            csrf_cookie = info.context.COOKIES[settings.CSRF_COOKIE_NAME]
            csrf_token = _sanitize_token(info.context.headers['X-Csrftoken'])

            if _compare_salted_tokens(csrf_cookie, csrf_token):
                return f(cls, self, info, **kwargs)
            else:
                raise GraphQLError("CSRF verification failed.")

        else:
            raise GraphQLError("CSRF verification failed.")

    return wrapper


class ImageFieldType(graphene.ObjectType):
    url = graphene.String()
    width = graphene.Int()
    height = graphene.Int()

    def resolve_url(self, info):
        if self.name:
            return self.url

        return ''

    def resolve_width(self, info):
        if self.name:
            return self.width

        return None

    def resolve_height(self, info):
        if self.name:
            return self.height

        return None


class BaseImageTypeMixin:
    original = graphene.Field(ImageFieldType)

    def resolve_large(self, info):
        if self.large is not None and self.large.name:
            return self.large.url

        return ''

    def resolve_medium(self, info):
        if self.medium is not None and self.medium.name:
            return self.medium.url

        return ''

    def resolve_small(self, info):
        if self.small is not None and self.small.name:
            return self.small.url

        return ''


class ImageInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    data = graphene.String(required=True)
    alttext = graphene.String(required=True)
    caption = graphene.String()


class PriceInput(graphene.InputObjectType):
    price_type = graphene.String(required=True)
    amount = graphene.Float()
    details = graphene.String()


class UploadInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    data = graphene.String(required=True)
    delete = graphene.Boolean()
    allow_downloads = graphene.Boolean()
    is_preview = graphene.Boolean()


class PriceGrapheneType(DjangoObjectType):
    class Meta:
        model = Price


class CountryType(DjangoObjectType):
    class Meta:
        model = Country


class IdentityType(DjangoObjectType):
    class Meta:
        model = Identity


class TagType(DjangoObjectType):
    class Meta:
        model = Tag


class FormatType(DjangoObjectType):
    class Meta:
        model = Format


class LengthType(DjangoObjectType):
    class Meta:
        model = Length


class GenreType(DjangoObjectType):
    class Meta:
        model = Genre


class LanguageType(DjangoObjectType):
    class Meta:
        model = Language


class DistributionTypeGrapheneType(DjangoObjectType):
    class Meta:
        model = DistributionType


class ContentRatingType(DjangoObjectType):
    class Meta:
        model = ContentRating


class SeoCategoryType(DjangoObjectType):
    class Meta:
        model = SeoCategory


class NameWithPriorityInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    priority = graphene.Int(required=True)


class LinkInput(NameWithPriorityInput):
    url = graphene.String(required=True)


class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    priority = graphene.Int(required=True)


class URLComponentsType(ObjectType):
    id = graphene.ID()
    slug = graphene.String()
    type = graphene.String()
    thread = graphene.Field('catalog.schema.schema_base.ThreadType')
    comment = graphene.Field('catalog.schema.schema_base.CommentType')


class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification

    type = graphene.String()
    message = graphene.String()
    url_components = graphene.Field(URLComponentsType)

    def resolve_type(self, info):
        return self.get_type()

    def resolve_message(self, info):
        return self.get_message()

    def resolve_url_components(self, info):
        return self.get_url_components()


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment

    timestamp = graphene.String()
    user_reaction = graphene.Boolean()
    reaction_count = graphene.Int()

    def resolve_timestamp(self, info):
        timedelta = timezone.now() - self.timestamp
        if timedelta.days > 0:
            return "{0}d".format(timedelta.days)
        seconds = timedelta.seconds
        if seconds >= 3600:
            hours = round(timedelta.seconds / 3600)
            return "{0}h".format(hours)
        if seconds >= 60:
            minutes = round(timedelta.seconds / 60)
            return "{0}m".format(minutes)
        if seconds == 0:
            return "Just now"

        return "{0}s".format(seconds)

    def resolve_user_reaction(self, info):
        if info.context.user.is_authenticated is False:
            return False

        if CommentReaction.objects.filter(comment=self, reactor=info.context.user).exists():
            return True

        return False

    def resolve_reaction_count(self, info):
        return CommentReaction.objects.filter(comment=self).count()


class ThreadType(DjangoObjectType):
    class Meta:
        model = Thread
        fields = ('id', 'originator', 'timestamp')

    comments = graphene.List(CommentType)

    def resolve_comments(self, info):
        return Comment.objects.filter(thread_id=self.id)


class ReactionGrapheneType(DjangoObjectType):
    class Meta:
        model = ReactionType


class CommentReactionType(DjangoObjectType):
    class Meta:
        model = CommentReaction


class UpdateComment(graphene.Mutation):
    thread = graphene.Field(ThreadType)

    class Arguments:
        comment = graphene.String(required=True)
        body = graphene.String()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        comment = kwargs.get('comment')
        body = kwargs.get('body')

        if Comment.objects.filter(id=comment).exists() is False:
            raise GraphQLError("Target comment does not exist! Please refresh or try again later")

        target_comment = Comment.objects.get(id=comment)

        if target_comment.commenter != info.context.user:
            raise GraphQLError("You are not authorized to update this comment")

        target_comment.body = body
        target_comment.is_edited = True
        target_comment.save()

        return UpdateComment(thread=target_comment.thread)


class SetCommentReaction(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        comment = graphene.String(required=True)
        reaction_type = graphene.String()
        delete = graphene.Boolean()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        comment = kwargs.get('comment')
        reaction_type = kwargs.get('reaction_type')
        delete = kwargs.get('delete')

        if Comment.objects.filter(id=comment).exists() is False:
            raise GraphQLError("Target comment does not exist! Please refresh or try again later")

        target_comment = Comment.objects.get(id=comment)

        if ReactionType.objects.filter(slug=reaction_type).exists() is False:
            raise GraphQLError("Reaction type is invalid")

        target_reaction_type = ReactionType.objects.get(slug=reaction_type)

        if CommentReaction.objects.filter(comment=target_comment, reactor=info.context.user).exists():
            reaction = CommentReaction.objects.get(comment=target_comment, reactor=info.context.user)

            if delete is True:
                reaction.delete()
                return SetCommentReaction(comment=target_comment)

            reaction.reaction_type = target_reaction_type
            reaction.save()
        else:
            reaction = CommentReaction(comment=target_comment, reactor=info.context.user, reaction_type=target_reaction_type)
            reaction.save()

        if info.context.user != target_comment.commenter:
            notification = Notification(content_object=reaction, notifier=info.context.user,
                                        recipient=target_comment.commenter)
            notification.save()

        return SetCommentReaction(comment=target_comment)


class BaseQuery(graphene.ObjectType):
    reaction_types = graphene.List(ReactionGrapheneType)

    def resolve_reaction_types(self, info):
        return ReactionType.objects.all()


class BaseMutation(graphene.ObjectType):
    update_comment = UpdateComment.Field()
    set_comment_reaction = SetCommentReaction.Field()


def GQLRatelimitKey(group, request):
    return request.gql_rl_field


def ratelimit(group=None, key=None, rate=None, message="Permission denied"):
    def decorator(fn):
        def _wrapped(cls, self, info, **kwargs):
            request = info.context
            old_limited = getattr(request, "limited", False)

            new_key = key
            if key and key.startswith("gql:"):
                _key = key.split("gql:")[1]
                value = kwargs.get(_key, None)
                if not value:
                    raise ValueError(f"Cannot get key: {key}")
                request.gql_rl_field = value

                new_key = GQLRatelimitKey

            ratelimited = is_ratelimited(
                request=request,
                group=group,
                fn=fn,
                key=new_key,
                rate=rate,
                increment=True,
            )

            if ratelimited or old_limited:
                raise Exception(message)
            return fn(cls, self, info, **kwargs)
        return _wrapped
    return decorator


def save_pdf_data(model_instance, model_attribute, file_data, file_name):
    prefix, filestr = file_data.split(';base64,')
    mime_type = prefix.split('/')[-1]

    if 'pdf' not in mime_type:
        raise TypeError('File must be in PDF format')

    filename, extension = os.path.splitext(file_name)

    file_buffer = base64.b64decode(filestr + "===")
    file_instance = ContentFile(file_buffer)
    upload_data = InMemoryUploadedFile(file_instance, None, file_name, 'application/pdf', len(file_instance), None,
                                       mime_type)
    getattr(model_instance, model_attribute).save(
        name="{0}{1}".format(filename, extension),
        content=upload_data,
        save=False)
    model_instance.save()


def save_image_data_via_model(model_instance, image_data, image_name):
    prefix, imgstr = image_data.split(';base64,')
    mime_type = prefix.split('/')[-1]

    if 'jpeg' not in mime_type and 'png' not in mime_type:
        raise TypeError('Images must be in JPEG or PNG format')

    filename, extension = os.path.splitext(image_name)

    opened_image = ImageUtils.open(BytesIO(base64.b64decode(imgstr + "===")))

    # Save an original image
    image_buffer = get_image_buffer(opened_image, mime_type)
    upload_data = InMemoryUploadedFile(image_buffer, None, image_name, 'text/plain', len(image_buffer), None,
                                       mime_type)
    getattr(model_instance, DEFAULT_IMAGE_SIZE_NAME).save(
        name="{0}-{1}{2}".format(filename, DEFAULT_IMAGE_SIZE_NAME, extension),
        content=upload_data,
        save=False)
    model_instance.save(skip_callback=False)


def save_image_data(image_path, image_data):
    prefix, imgstr = image_data.split(';base64,')
    mime_type = prefix.split('/')[-1]

    if 'jpeg' not in mime_type and 'png' not in mime_type:
        raise TypeError('Images must be in JPEG or PNG format')

    opened_image = ImageUtils.open(BytesIO(base64.b64decode(imgstr + "===")))

    # Save an original image
    image_buffer = get_image_buffer(opened_image, mime_type)
    upload_data = InMemoryUploadedFile(image_buffer, None, image_path, 'text/plain', len(image_buffer), None,
                                       mime_type)

    storage = CatalogImageStorage()
    return storage.save(image_path, upload_data)


def create_presigned_url(object_name, expiration=3600):

    s3_client = boto3.client('s3', config=Config(
        region_name=settings.AWS_S3_REGION_NAME,
        signature_version='s3v4'
    ))
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error("there was an error")
        logging.error(e)
        raise GraphQLError("Unable to create download URL! Please try again later.")

    # The response contains the presigned URL
    return response


def send_membership_email(organization_name, invite_type, invitee_email):

    subject = "Confirm membership to {0}".format(organization_name)
    title = "Confirm Membership"
    message = ("You've been added to {0} as a(n) {1}. "
                   "To display this membership on you profile, log into your account to complete the request. "
                   "You can also delete the request from within your account.").format(organization_name, invite_type)

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(email="info@altsalt.com", name="AltSalt")
    to_email = To(invitee_email)

    log_in_url = '{0}/user/login'.format(os.environ.get('BASE_URL'))
    mail = Mail(from_email, to_email, subject)
    mail.dynamic_template_data = {
        'subject': subject,
        'title': title,
        'message': message,
        'log_in_url': log_in_url,
        "name": "AltSalt",
    }
    mail.template_id = 'd-8937eb33fafb473d9603ef921ba8d184'
    response = sg.client.mail.send.post(request_body=mail.get())


def send_byline_email(inviter_name, listing_title, invitee_email, invite_type):

    subject = "Confirm byline on {0}".format(listing_title)
    title = "Confirm a New Byline"
    message = ("You've been added as a {0} on {1} by {2}. "
                   "To display this byline on your profile, log into your account to complete the request. "
                   "You can also delete the request from within your account.").format(invite_type, listing_title, inviter_name)

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(email="info@altsalt.com", name="AltSalt")
    to_email = To(invitee_email)

    log_in_url = '{0}/user/login'.format(os.environ.get('BASE_URL'))
    mail = Mail(from_email, to_email, subject)
    mail.dynamic_template_data = {
        'subject': subject,
        'title': title,
        'message': message,
        'log_in_url': log_in_url,
        "name": "AltSalt",
    }
    mail.template_id = 'd-8937eb33fafb473d9603ef921ba8d184'
    response = sg.client.mail.send.post(request_body=mail.get())


def send_moderator_notification_email(target_email, submission_title):
    subject = "New AltSalt submission {0}".format(submission_title)
    title = "We received a new submission! - {0}".format(submission_title)

    message = ("To view this submission, go to the moderator tools "
               "inside of your AltSalt account.")

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(email="info@altsalt.com", name="AltSalt")
    to_email = To(target_email)

    log_in_url = '{0}/user/login'.format(os.environ.get('BASE_URL'))
    mail = Mail(from_email, to_email, subject)
    mail.dynamic_template_data = {
        'subject': subject,
        'title': title,
        'message': message,
        'log_in_url': log_in_url,
        "name": "AltSalt",
    }
    mail.template_id = 'd-8937eb33fafb473d9603ef921ba8d184'
    response = sg.client.mail.send.post(request_body=mail.get())


def send_submission_approved_email(target_username, submission_title, target_email, message):
    subject = "{0}, your submission {1} has been approved".format(target_username, submission_title)
    title = "Create a New Listing for {0}".format(submission_title)

    if message is None or message.strip() == '':
        body = ("Your submission has been approved! "
                "To display this work on your profile, "
                "please log into your account to create a listing. ")
    else:
        body = message

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(email="info@altsalt.com", name="AltSalt")
    to_email = To(target_email)

    log_in_url = '{0}/user/login'.format(os.environ.get('BASE_URL'))
    mail = Mail(from_email, to_email, subject)
    mail.dynamic_template_data = {
        'subject': subject,
        'title': title,
        'message': body,
        'log_in_url': log_in_url,
        "name": "AltSalt",
    }
    mail.template_id = 'd-8937eb33fafb473d9603ef921ba8d184'
    response = sg.client.mail.send.post(request_body=mail.get())


def send_listing_public_email(target_username, listing_title, target_email):
    subject = "{0}, your listing {1} is public!".format(target_username, listing_title)
    title = "{0} is now on AltSalt".format(listing_title)

    message = ("We approved your listing and it will "
            "appear to everyone who visits AltSalt shortly (it may take an hour or so "
            "for the changes to propagate).")

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(email="info@altsalt.com", name="AltSalt")
    to_email = To(target_email)

    mail = Mail(from_email, to_email, subject)
    mail.dynamic_template_data = {
        'subject': subject,
        'title': title,
        'message': message,
        "name": "AltSalt",
    }
    mail.template_id = 'd-7bbf18f8831c4783be50a0ab93f4d8ac'
    response = sg.client.mail.send.post(request_body=mail.get())


def send_submission_rejected_email(target_username, submission_title, target_email, message):
    subject = "{0}, your submission {1} was not approved".format(target_username, submission_title)
    title = "Thank you for submitting to AltSalt!"

    if message is None or message.strip() == '':
        body = ("We appreciate you submitting to AltSalt. "
                "We did not approve your submission, either because it's not a good fit "
                "or it violated our community guidelines. However, we invite you to submit again in the future! ")
    else:
        body = message

    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    from_email = Email(email="info@altsalt.com", name="AltSalt")
    to_email = To(target_email)

    mail = Mail(from_email, to_email, subject)
    mail.dynamic_template_data = {
        'subject': subject,
        'title': title,
        'message': body,
        "name": "AltSalt",
    }
    mail.template_id = 'd-7bbf18f8831c4783be50a0ab93f4d8ac'
    response = sg.client.mail.send.post(request_body=mail.get())


def send_welcome_email(user, is_test):
    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

    from_confirmation_email = Email(email="artemio@altsalt.com", name="AltSalt")

    token = GenerateRandomString()
    notification_settings_authorized_update = NotificationSettingsAuthorizedUpdate(user=user,
                                                                                   token=make_password(token))
    notification_settings_authorized_update.save()

    email_preferences_url = "{0}/user/email-preferences?id={1}&requestId={2}&token={3}".format(
        os.environ.get('BASE_URL'), user.id, notification_settings_authorized_update.id, token)
    unsubscribe_url = "{0}&frequency={1}".format(email_preferences_url, NotificationSettings.Frequency.OFF)

    to_confirmation_email = To(user.email)
    welcome_email = Mail(from_confirmation_email, to_confirmation_email)
    welcome_email.dynamic_template_data = {
        "email_preferences_url": email_preferences_url,
        "unsubscribe_url": unsubscribe_url
    }

    if is_test:
        welcome_email.category = Category('Welcome Email Test {0}'.format(os.environ.get('BASE_URL')))
    else:
        welcome_email.category = Category('Welcome Email {0}'.format(os.environ.get('BASE_URL')))

    welcome_email.template_id = 'd-8b1a6243a78644e6a985c51fc2a4c1ee'
    response = sg.client.mail.send.post(request_body=welcome_email.get())

    return True

