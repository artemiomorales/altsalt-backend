import graphene
from catalog.models.base import Country, Identity
from catalog.models.listing import Price
from graphene_django.types import DjangoObjectType
from django.conf import settings
from django.middleware.csrf import _sanitize_token, _compare_salted_tokens
from graphql import GraphQLError

import os
import base64
import PIL.Image as ImageUtils
from django.core.files.base import ContentFile
from django.core.files.uploadhandler import InMemoryUploadedFile
from io import BytesIO

from catalog.constants import DEFAULT_IMAGE_SIZE_NAME, get_image_buffer
from botocore.exceptions import ClientError
import boto3
from botocore.config import Config

# Email

import logging
import sendgrid
from sendgrid.helpers.mail import *


# Rate limiting

from ratelimit.core import is_ratelimited


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


class PriceInput(graphene.InputObjectType):
    price_type = graphene.String(required=True)
    amount = graphene.Float()
    details = graphene.String()


class UploadInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    data = graphene.String(required=True)
    delete = graphene.Boolean()
    allow_downloads = graphene.Boolean()


class PriceGrapheneType(DjangoObjectType):
    class Meta:
        model = Price


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


def GQLRatelimitKey(group, request):
    return request.gql_rl_field


def ratelimit(group=None, key=None, rate=None, message="Permission denied"):
    def decorator(fn):
        def _wrapped(cls, self, info, **kwargs):
            request = info.context
            old_limited = getattr(request, "limited", False)

            logging.error(kwargs)

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

    logging.error(mime_type)

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


def save_image_data(model_instance, image_data, image_name):
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


class CountryType(DjangoObjectType):
    class Meta:
        model = Country


class IdentityType(DjangoObjectType):
    class Meta:
        model = Identity


class NameWithPriorityInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    priority = graphene.Int(required=True)


class LinkInput(NameWithPriorityInput):
    url = graphene.String(required=True)


class UserInput(graphene.InputObjectType):
    username = graphene.String(required=True)
    priority = graphene.Int(required=True)


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