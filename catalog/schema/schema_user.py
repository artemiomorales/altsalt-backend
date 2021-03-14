from datetime import date
from django.contrib.auth import get_user_model
from catalog.models.base import Notification
from catalog.models.cms import *
from catalog.models.user import *
from catalog.models.listing import *
from catalog.models.submission import *
from catalog.utils import GenerateRandomString

import re
import graphene
from graphene_django.types import DjangoObjectType, ObjectType
from graphql_jwt.decorators import login_required, token_auth
from .schema_base import check_csrf, save_image_data, BaseImageTypeMixin, CountryType, IdentityType, LinkInput, \
    NameWithPriorityInput, UserInput, send_membership_email, ratelimit, NotificationType, send_welcome_email
from .schema_cms import ArticleBylineType
from .schema_listing import ListingCreatorBylineType, ListingCollaboratorBylineType

from django.contrib.auth.hashers import make_password, check_password
import os

from graphql import GraphQLError
from django.template.defaultfilters import slugify

from catalog.data.restricted_terms.restricted_usernames import is_restricted_username
from catalog.data.restricted_terms.restricted_fragments import is_restricted_fragment

# Image handling
import base64
import PIL.Image as ImageUtils
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from catalog.constants import capitalize_string

# Email
import sendgrid
from sendgrid.helpers.mail import *

# jwt
import graphql_jwt
from graphql_jwt.decorators import signals,\
    on_token_auth_resolve, wraps, setup_jwt_cookie, csrf_rotation, refresh_expiration, maybe_thenable
from graphql_jwt.mixins import JSONWebTokenMixin, ResolveMixin
from graphql_jwt.refresh_token.models import RefreshToken

from catalog.constants import get_date_from_string

# recaptcha
import requests

from catalog.tasks import send_digest_email

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)


#########
# TYPES #
#########


class OrganizationMemberType(DjangoObjectType):
    class Meta:
        model = OrganizationMember
        exclude = ('member',)

    user = graphene.Field(lambda: UserType)

    def resolve_user(self, info):
        return get_user_model().objects.get(id=self.member_id)


class UserCountryType(DjangoObjectType):
    class Meta:
        model = UserCountry
        exclude = ('country',)

    item = graphene.Field(CountryType)

    def resolve_item(self, info):
        return Country.objects.get(id=self.country_id)


class UserIdentityType(DjangoObjectType):
    class Meta:
        model = UserIdentity
        exclude = ('identity',)

    item = graphene.Field(IdentityType)

    def resolve_item(self, info):
        return Identity.objects.get(id=self.identity_id)


class UserLinkType(DjangoObjectType):
    class Meta:
        model = UserLink


class InvitationType(DjangoObjectType):
    class Meta:
        model = Invitation


class ResetPasswordRequestType(DjangoObjectType):
    class Meta:
        model = ResetPasswordRequest


class UserProfileImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = UserProfileImage


class NotificationSettingsComponentsType(ObjectType):
    label = graphene.String()
    value = graphene.String()
    description = graphene.String()


class NotificationSettingsType(DjangoObjectType):
    class Meta:
        model = NotificationSettings

    frequency = graphene.Field(NotificationSettingsComponentsType)
    choices = graphene.List(NotificationSettingsComponentsType)

    def resolve_frequency(self, info):
        return {'label': dict(self.Frequency.choices)[self.frequency],
                'value': self.frequency,
                'description': self.get_frequency_description(self.frequency)}

    def resolve_choices(self, info):
        choices_array = []
        for value in self.Frequency.values:
            choices_array.append({'label': dict(self.Frequency.choices)[value],
                                  'value': value,
                                  'description': self.get_frequency_description(value)})
        return choices_array


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ('id', 'is_moderator', 'is_verified', 'username', 'first_name', 'display_name', 'short_name', 'occupation',
                  'description', 'is_organization', 'date_of_birth', 'show_age', 'pronouns', 'location', 'date_joined', 'is_superuser')

    profile_image = graphene.Field(UserProfileImageType)
    listings = graphene.List(ListingCreatorBylineType)
    collaborations = graphene.List(ListingCollaboratorBylineType)
    articles = graphene.List(ArticleBylineType)
    countries = graphene.List(UserCountryType)
    identities = graphene.List(UserIdentityType)
    age = graphene.Int()
    links = graphene.List(UserLinkType)
    date_joined = graphene.String()
    organizations = graphene.List(OrganizationMemberType)
    admins = graphene.List(OrganizationMemberType)
    members = graphene.List(OrganizationMemberType)
    submissions = graphene.List('catalog.schema.schema_submission.SubmissionType')
    invitations_remaining = graphene.Int()
    unread_notifications_count = graphene.Int()
    notifications = graphene.List(NotificationType, count=graphene.Int())
    notification_settings = graphene.Field(NotificationSettingsType)

    def resolve_listings(self, info):
        return ListingCreatorByline.objects.filter(user_id=self.id)

    def resolve_collaborations(self, info):
        return ListingCollaboratorByline.objects.filter(user_id=self.id)

    def resolve_articles(self, info):
        return ArticleByline.objects.filter(user_id=self.id)

    def resolve_organizations(self, info):
        return OrganizationMember.objects.filter(member_id=self.id)

    def resolve_admins(self, info):
        if self.is_organization is True:
            return OrganizationMember.objects.filter(organization_id=self.id, is_admin=True)

        return None

    def resolve_members(self, info):
        if self.is_organization is True:
            return OrganizationMember.objects.filter(organization_id=self.id, is_admin=False)

        return None

    def resolve_countries(self, info):
        return UserCountry.objects.filter(user_id=self.id)

    def resolve_identities(self, info):
        return UserIdentity.objects.filter(user_id=self.id)

    def resolve_profile_image(self, info):
        if UserProfileImage.objects.filter(user_id=self.id).exists() is True:
            return UserProfileImage.objects.get(user_id=self.id)

        return None

    def resolve_age(self, info):
        if self.date_of_birth is not None:
            born = self.date_of_birth
            today = date.today()
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

        return None

    def resolve_links(self, info):
        return UserLink.objects.filter(user_id=self.id)

    def resolve_date_joined(self, info):
        return self.date_joined.strftime("%m/%d/%y")

    def resolve_submissions(self, info):
        return Submission.objects.filter(creator=self)

    def resolve_invitations_remaining(self, info):
        if self.is_moderator:
            return -1

        invitation_count = Invitation.objects.filter(requester=self).count()
        return 2 - invitation_count

    def resolve_unread_notifications_count(self, info):
        if info.context.user == self:
            return Notification.objects.filter(recipient=self, is_read=False).count()

        return None

    def resolve_notifications(self, info, **kwargs):

        count = kwargs.get('count')

        if info.context.user == self:
            if count is not None and count != -1:
                return Notification.objects.filter(recipient=self)[:count]
            return Notification.objects.filter(recipient=self)

        return None

    def resolve_notification_settings(self, info):
        return self.notificationsettings


#########
# UTILS #
#########






##########
# LOG IN #
##########

class LogIn(graphql_jwt.ObtainJSONWebToken):
    user = graphene.Field(UserType)

    @classmethod
    @ratelimit(group="login", key="gql:username", rate="6/5m",
               message="Max number of login attempts reached. Your account has been temporarily locked."
                       " Please consider resetting your password, and try again later.")
    @ratelimit(group="login", key="ip", rate="6/5m",
               message="Max number of login attempts reached. Your device has been temporarily restricted."
                       " Please consider resetting your password, and try again later.")
    @token_auth
    def mutate(cls, root, info, **kwargs):
        return cls.resolve(root, info, **kwargs)

    @classmethod
    @check_csrf
    def resolve(cls, root, info, **kwargs):
        if info.context.user.is_candidate:
            raise GraphQLError("Email address not verified! Please click the link we sent "
                               "to your email to finish creating your account.")
        return cls(user=info.context.user)


###############
# UPDATE USER #
###############

class UserMembershipInput(graphene.InputObjectType):
    organization_username = graphene.String(required=True)
    priority = graphene.Int(required=True)
    delete = graphene.Boolean(required=True)


class UserBylineInput(graphene.InputObjectType):
    id = graphene.String(required=True)
    priority = graphene.Int(required=True)
    delete = graphene.Boolean(required=True)


def CreateProfileThumbnail(imgstr, ext, profile_image_name, user_profile_image, size_name, size_dimensions):
    opened_image = ImageUtils.open(BytesIO(base64.b64decode(imgstr + "===")))

    responsive_sizes = [1, 2, 3, 4]
    for responsive_size in responsive_sizes:
        buffer = BytesIO()
        resize_image = opened_image.copy()
        resize_image.thumbnail((size_dimensions * responsive_size, size_dimensions * responsive_size))
        resize_image.save(fp=buffer, format=ext, optimize=True)
        data = ContentFile(buffer.getvalue())

        filename, file_extension = os.path.splitext(profile_image_name)

        save_name = "{0}-{1}-{2}x{3}".format(filename, size_name, responsive_size, file_extension)

        if responsive_size == 1:
            getattr(user_profile_image, size_name).save(name=save_name, content=data)
        else:
            default_storage.save(save_name, data)


def DeleteProfileThumbnail(img_name):
    filename, file_extension = os.path.splitext(img_name)
    responsive_sizes = [1, 2, 3, 4]
    for responsive_size in responsive_sizes:
        default_storage.delete("{0}-{1}x{2}".format(filename, responsive_size, file_extension))


class UpdateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        profile_image_name = graphene.String()
        profile_image = graphene.String()
        display_name = graphene.String()
        short_name = graphene.String()
        occupation = graphene.String()
        description = graphene.String()
        date_of_birth = graphene.String()
        links = graphene.List(LinkInput)
        show_age = graphene.Boolean()
        pronouns = graphene.String()
        location = graphene.String()
        countries = graphene.List(NameWithPriorityInput)
        identities = graphene.List(NameWithPriorityInput)
        creator_bylines = graphene.List(UserBylineInput)
        collaborator_bylines = graphene.List(UserBylineInput)
        organizations = graphene.List(UserMembershipInput)
        is_organization = graphene.Boolean()
        admins = graphene.List(UserInput)
        members = graphene.List(UserInput)

    @classmethod
    @check_csrf
    def mutate(cls, self, info, **kwargs):
        username = kwargs.get('username')

        if info.context.user.username != username:
            raise GraphQLError("You are not authorized to update this user.")

        if get_user_model().objects.filter(username=username).exists() is False:
            raise GraphQLError("Target user does not exist.")

        target_user = get_user_model().objects.get(username=username)

        display_name = kwargs.get('display_name')
        short_name = kwargs.get('short_name')
        profile_image_name = kwargs.get('profile_image_name')
        profile_image = kwargs.get('profile_image')
        occupation = kwargs.get('occupation')
        description = kwargs.get('description')
        date_of_birth = kwargs.get('date_of_birth')
        links = kwargs.get('links')
        show_age = kwargs.get('show_age')
        pronouns = kwargs.get('pronouns')
        location = kwargs.get('location')
        countries = kwargs.get('countries')
        identities = kwargs.get('identities')
        creator_bylines = kwargs.get('creator_bylines')
        collaborator_bylines = kwargs.get('collaborator_bylines')
        organizations = kwargs.get('organizations')
        is_organization = kwargs.get('is_organization')
        admins = kwargs.get('admins')
        members = kwargs.get('members')

        if profile_image_name != '' and profile_image is not None:

            if UserProfileImage.objects.filter(user=target_user).exists() is True:
                current_image = UserProfileImage.objects.get(user=target_user)
            else:
                current_image = UserProfileImage(user=target_user)
                current_image.save(skip_callback=True)

            save_image_data(current_image, profile_image, profile_image_name)

        if display_name is not None:
            target_user.display_name = display_name

        if short_name is not None:
            target_user.short_name = short_name

        if occupation is not None:
            target_user.occupation = occupation

        if description is not None:
            target_user.description = description

        if date_of_birth is not None:
            if date_of_birth == '':
                target_user.date_of_birth = None
            else:
                target_user.date_of_birth = get_date_from_string(date_of_birth)

        existing_links = UserLink.objects.filter(user=target_user.id)
        existing_links.delete()

        if links is not None:
            for link in links:
                new_link = UserLink(user=target_user, name=link.name, url=link.url, priority=link.priority)
                new_link.save()

        if show_age is not None:
            target_user.show_age = show_age

        if pronouns is not None:
            target_user.pronouns = pronouns

        if location is not None:
            target_user.location = location

        existing_countries = UserCountry.objects.filter(user=target_user)
        existing_countries.delete()

        if countries is not None:
            for country in countries:
                item_slug = slugify(country.name)
                if Country.objects.filter(slug=item_slug).exists() is False:
                    new_country = Country(name=country.name.capitalize(), slug=item_slug)
                    new_country.save()

                item_object = Country.objects.get(slug=item_slug)
                user_country = UserCountry(user=target_user, country=item_object, priority=country.priority)
                user_country.save()

        existing_identities = UserIdentity.objects.filter(user=target_user)
        existing_identities.delete()

        if identities is not None:
            for identity in identities:
                item_slug = slugify(identity.name)
                if Identity.objects.filter(slug=item_slug).exists() is False:
                    new_identity = Identity(name=capitalize_string(identity.name), slug=item_slug)
                    new_identity.save()

                item_object = Identity.objects.get(slug=item_slug)
                user_identity = UserIdentity(user=target_user, identity=item_object, priority=identity.priority)
                user_identity.save()

        if creator_bylines is not None:
            for creator_byline in creator_bylines:
                if Listing.objects.filter(id=creator_byline.id).exists() is True:
                    target_listing = Listing.objects.get(id=creator_byline.id)
                    if ListingCreatorByline.objects.filter(user=target_user, listing=target_listing).exists() is True:
                        byline = ListingCreatorByline.objects.get(user=target_user, listing=target_listing)

                        if creator_byline.delete is True:
                            raise GraphQLError('Creator bylines should not be deleted from '
                                               'the user page; try editing a listing instead')
                        else:
                            byline.user_priority = creator_byline.priority
                            byline.save()

        if collaborator_bylines is not None:
            for collaborator_byline in collaborator_bylines:
                if Listing.objects.filter(id=collaborator_byline.id).exists() is True:
                    target_listing = Listing.objects.get(id=collaborator_byline.id)
                    if ListingCollaboratorByline.objects.filter(user=target_user, listing=target_listing).exists() is True:
                        byline = ListingCollaboratorByline.objects.get(user=target_user, listing=target_listing)

                        if collaborator_byline.delete is True:
                            byline.delete()
                        else:
                            byline.user_priority = collaborator_byline.priority
                            byline.save()

        if organizations is not None:
            for organization in organizations:
                if get_user_model().objects.filter(username=organization.organization_username).exists() is True:
                    organization_item = get_user_model().objects.get(username=organization.organization_username)
                    if OrganizationMember.objects.filter(organization=organization_item, member=target_user).exists() is True:
                        role = OrganizationMember.objects.get(organization=organization_item, member=target_user)

                        if organization.delete is True:
                            role.delete()
                        else:
                            role.user_priority = organization.priority
                            role.save()

        if is_organization is not None:
            target_user.is_organization = is_organization


        if admins is not None:

            existing_admin_roles = OrganizationMember.objects.filter(organization=target_user, is_admin=True)
            for existing_admin_role in existing_admin_roles:
                delete_existing_byline = True
                for admin in admins:
                    if get_user_model().objects.filter(username=admin.username).exists() and \
                       existing_admin_role.member.username == admin.username:
                        delete_existing_byline = False
                if delete_existing_byline:
                    existing_admin_role.delete()

            for admin in admins:
                if get_user_model().objects.filter(username=admin.username).exists():
                    stored_user = get_user_model().objects.get(username=admin.username)
                    if OrganizationMember.objects.filter(organization=target_user, member=stored_user).exists():
                        membership = OrganizationMember.objects.get(organization=target_user, member=stored_user)
                        membership.organization_priority = admin.priority
                        membership.is_admin = True
                    else:
                        membership = OrganizationMember(organization=target_user, member=stored_user,
                                                              organization_priority=admin.priority, is_admin=True)
                        send_membership_email(target_user.display_name, 'admin', stored_user.email)
                    membership.save()
                else:
                    raise GraphQLError(
                        'Specified user {0} does not exist. Please remove and try again'.format(admin.username))


        if members is not None:

            existing_member_roles = OrganizationMember.objects.filter(organization=target_user, is_admin=False)
            for existing_member_role in existing_member_roles:
                delete_existing_byline = True
                for member in members:
                    if get_user_model().objects.filter(username=member.username).exists() and \
                            existing_member_role.member.username == member.username:
                        delete_existing_byline = False
                if delete_existing_byline:
                    existing_member_role.delete()

            for member in members:
                if get_user_model().objects.filter(username=member.username).exists():
                    stored_user = get_user_model().objects.get(username=member.username)
                    if OrganizationMember.objects.filter(organization=target_user, member=stored_user).exists():
                        membership = OrganizationMember.objects.get(organization=target_user, member=stored_user)
                        membership.organization_priority = member.priority
                        membership.is_admin = False
                    else:
                        membership = OrganizationMember(organization=target_user, member=stored_user,
                                                        organization_priority=member.priority, is_admin=False)
                        send_membership_email(target_user.display_name, 'member', stored_user.email)
                    membership.save()
                else:
                    raise GraphQLError(
                        'Specified user {0} does not exist. Please remove and try again'.format(member.username))


        target_user.save()

        return UpdateUser(user=target_user)


#######################
# UPDATE NOTIFICATION #
#######################

class UpdateNotifications(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        notifications = graphene.List(graphene.String)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        target_notifications = kwargs.get('notifications')

        ## For now, this mutation just marks all as read
        if target_notifications is None:
            notifications = Notification.objects.filter(recipient=info.context.user)
            for notification in notifications:
                notification.is_read = True
                notification.save()
            return UpdateNotifications(user=info.context.user)

        return None


##################
# CONFIRM BYLINE #
##################

class ConfirmByline(graphene.Mutation):
    user = graphene.Field(UserType)
    confirmed = graphene.Boolean()

    class Arguments:
        id = graphene.String(required=True)
        target_status = graphene.Boolean(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, id, target_status):

        if Listing.objects.filter(id=id).exists() is False:
            raise GraphQLError("Target listing does not exist! Please refresh or try again later.")

        target_listing = Listing.objects.get(id=id)

        target_byline = None

        if ListingCreatorByline.objects.filter(listing=target_listing, user=info.context.user).exists():
            target_byline = ListingCreatorByline.objects.get(listing=target_listing, user=info.context.user)

        if ListingCollaboratorByline.objects.filter(listing=target_listing, user=info.context.user).exists():
            target_byline = ListingCollaboratorByline.objects.get(listing=target_listing, user=info.context.user)

        if target_byline is None:
            raise GraphQLError("You are not authorized to update this byline.")

        if target_status:
            target_byline.is_confirmed = True
            target_byline.save()
            return ConfirmByline(user=info.context.user, confirmed=True)
        else:
            target_byline.delete()
            return ConfirmByline(user=info.context.user, confirmed=False)


######################
# CONFIRM MEMBERSHIP #
######################

class ConfirmMembership(graphene.Mutation):
    user = graphene.Field(UserType)
    confirmed = graphene.Boolean()

    class Arguments:
        organization_username = graphene.String(required=True)
        target_status = graphene.Boolean(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, organization_username, target_status):

        if get_user_model().objects.filter(username=organization_username).exists() is False:
            raise GraphQLError("Target user does not exist! Please refresh or try again later.")

        organization = get_user_model().objects.get(username=organization_username)

        if OrganizationMember.objects.filter(organization=organization, member=info.context.user).exists():
            target_membership = OrganizationMember.objects.get(organization=organization, member=info.context.user)
        else:
            raise GraphQLError("Unable to update membership! Please refresh or try again later.")

        if target_status:
            target_membership.is_confirmed = True
            target_membership.save()
            return ConfirmMembership(user=info.context.user, confirmed=True)
        else:
            target_membership.delete()
            return ConfirmMembership(user=info.context.user, confirmed=False)


####################
# ACCOUNT CREATION #
####################

def verify_signup_code(invite_token=''):

    from os.path import join, dirname
    from dotenv import load_dotenv

    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    closed_signups_enabled = True if os.environ.get('CLOSED_SIGNUPS_ENABLED') == 'True' else False

    if closed_signups_enabled is True and\
            SignupCode.objects.filter(code=invite_token, active=True).exists():
        return True

    return False


def verify_personal_invitation(email, invite_token=''):

    if Invitation.objects.filter(email=email, redeemed=False).exists() is False:
        return False

    invitation = Invitation.objects.get(email=email, redeemed=False)
    encrypted_token = invitation.token
    return check_password(invite_token, encrypted_token)


class SendInvitation(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        invite_email = graphene.String(required=True)
        is_test = graphene.Boolean()
        subject = graphene.String()
        title = graphene.String()
        message = graphene.String()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        invitation_count = Invitation.objects.filter(requester=info.context.user).count()

        if info.context.user.is_moderator is False and invitation_count >= 2:
            raise GraphQLError('No invitations left!')

        is_test = kwargs.get("is_test")

        if is_test is True:
            invite_email = info.context.user.email
        else:
            invite_email = kwargs.get('invite_email')
            if Invitation.objects.filter(email=invite_email).exists() is True:
                raise GraphQLError('Specified user has already been invited!')
            if get_user_model().objects.filter(email=invite_email).exists() is True:
                raise GraphQLError('User with specified email already exists!')

        subject = kwargs.get('subject')
        if subject is None:
            subject = "Your submission to AltSalt has been approved"
        if is_test is True:
            subject = "TEST - {0}".format(subject)

        title = kwargs.get('title')
        if title is None:
            title = "Welcome to AltSalt!"
        message = kwargs.get('message')
        if message is None:
            message = ("We reviewed your recent submission to {0} and "
                       "would like to invite you create an account. Thanks so much for your interest "
                       "in helping to build this resource. We look forward to listing your work "
                       "and having you as part of the community!").format(os.environ.get('BASE_URL'))
        invite_token = GenerateRandomString()

        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        from_email = Email(email="info@altsalt.com", name="AltSalt")
        to_email = To(invite_email)

        sign_up_url = '{0}/user/signup'.format(os.environ.get('BASE_URL'))
        redeem_url = (sign_up_url + '?inviteEmail={0}&inviteToken={1}').format(invite_email, invite_token)

        mail = Mail(from_email, to_email, subject)
        mail.dynamic_template_data = {
            'subject': subject,
            'title': title,
            'message': message,
            'button_text': 'Create Account',
            'sign_up_url': sign_up_url,
            'redeem_url': redeem_url,
            'token': invite_token
        }
        mail.template_id = 'd-171f495feafe4472b043d3de1233b998'

        if is_test:
            mail.category = Category('Invitation Test {0}'.format(os.environ.get('BASE_URL')))
            response = sg.client.mail.send.post(request_body=mail.get())
            new_invitation = Invitation(email=invite_email, token=make_password(invite_token), requester=info.context.user)
            return SendInvitation(user=info.context.user)

        else:
            mail.category = Category('Invitation {0}'.format(os.environ.get('BASE_URL')))
            response = sg.client.mail.send.post(request_body=mail.get())
            new_invitation = Invitation(email=invite_email, token=make_password(invite_token), requester=info.context.user)
            new_invitation.save()
            return SendInvitation(user=info.context.user)


class UserCreationType(graphene.Enum):
    UNVERIFIED = 0
    CANDIDATE = 1
    FULL = 2


class VerifyUserCreationCode(graphene.Mutation):
    user_creation_type = graphene.Field(UserCreationType)

    class Arguments:
        invite_email = graphene.String(required=True)
        invite_token = graphene.String(required=True)

    @classmethod
    # @ratelimit(group="verify_invitation", key="ip", rate="5/hr",
    #            message="Max number of attempts reached. Your device has been temporarily restricted."
    #                    " Please try again later.")
    @check_csrf
    def mutate(cls, self, info, invite_email, invite_token):

        if verify_signup_code(invite_token) is True:
            return VerifyUserCreationCode(user_creation_type=UserCreationType.CANDIDATE)

        if verify_personal_invitation(invite_email, invite_token) is True:
            return VerifyUserCreationCode(user_creation_type=UserCreationType.FULL)

        raise GraphQLError('Invitation has expired or is invalid. Did you input the fields correctly?')


def validate_and_create_user(invite_email, username, first_name, last_name, password, is_candidate):
    if get_user_model().objects.filter(email=invite_email).exists() is True:
        existing_user = get_user_model().objects.get(email=invite_email)
        if existing_user.is_candidate:
            existing_user.delete()
        else:
            raise GraphQLError('User with specified email already exists')

    if get_user_model().objects.filter(username=username).exists() is True or \
            is_restricted_username(username) is True or \
            is_restricted_fragment(username) is True:
        raise GraphQLError('Username is not available')

    if re.match('^[a-zA-Z0-9_.-]+$', username) is None:
        raise GraphQLError('Username may only contain letters, numbers, hyphens, underscores, and periods')

    new_user = get_user_model()(
        first_name=first_name,
        last_name=last_name,
        display_name=first_name + ' ' + last_name,
        username=username.lower(),
        email=invite_email,
        is_candidate=is_candidate
    )
    new_user.set_password(password)
    new_user.save()

    return new_user


def create_user_mutate_wrapper(f):
    @wraps(f)
    @setup_jwt_cookie
    @csrf_rotation
    @refresh_expiration
    def wrapper(cls, root, info, **kwargs):
        invite_email = kwargs.get('invite_email')
        invite_token = kwargs.get('invite_token')
        username = kwargs.get('username')
        first_name = kwargs.get('first_name')
        last_name = kwargs.get('last_name')
        password = kwargs.get('password')

        if verify_personal_invitation(invite_email, invite_token) is False:
            raise GraphQLError('Invitation is invalid')

        else:
            new_user = validate_and_create_user(invite_email, username, first_name, last_name, password, False)

            invitation = Invitation.objects.get(email=invite_email)
            invitation.redeemed = True
            invitation.save()

            try:
                send_welcome_email(new_user, False)
            except:
                pass

            context = info.context
            context._jwt_token_auth = True

            if hasattr(context, 'user'):
                context.user = new_user

            result = f(cls, root, info, **kwargs)
            signals.token_issued.send(sender=cls, request=context, user=new_user)
            return maybe_thenable((context, new_user, result), on_token_auth_resolve)

    return wrapper


class CreateFullUser(ResolveMixin, JSONWebTokenMixin, graphene.Mutation):

    class Arguments:
        invite_email = graphene.String(required=True)
        invite_token = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    @classmethod
    @ratelimit(group="create_full_user", key="ip", rate="12/hr",
               message="Max number of requests reached. Your device has been temporarily restricted."
                       " Please try again later.")
    @check_csrf
    @create_user_mutate_wrapper
    def mutate(cls, root, info, **kwargs):
        return cls.resolve(root, info, **kwargs)


class CreateCandidateUser(graphene.Mutation):
    email = graphene.String()

    class Arguments:
        invite_token = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        recaptcha = graphene.String(required=True)

    @classmethod
    @check_csrf
    def mutate(cls, root, info, **kwargs):
        invite_token = kwargs.get('invite_token')
        email = kwargs.get('email')
        username = kwargs.get('username')
        first_name = kwargs.get('first_name')
        last_name = kwargs.get('last_name')
        password = kwargs.get('password')
        recaptcha = kwargs.get('recaptcha')

        from os.path import join, dirname
        from dotenv import load_dotenv

        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path)

        if verify_signup_code(invite_token) is False:
            open_signups_enabled = True if os.environ.get('OPEN_SIGNUPS_ENABLED') == 'True'\
                else False
            if open_signups_enabled is False:
                raise GraphQLError('Invitation code is invalid, and open signups are closed. '
                                   'Please try again or apply for an account.')

        url = 'https://www.google.com/recaptcha/api/siteverify'
        values = {
            'secret': os.environ.get('RECAPTCHA_SECRET_KEY'),
            'response': recaptcha
        }

        result = requests.post(url, data=values).json()

        if not result['success']:
            raise GraphQLError('Captcha is invalid. Please try again.')

        candidate_user = validate_and_create_user(email, username, first_name, last_name, password, True)

        if SignupCode.objects.filter(code=invite_token).exists():
            signup_code = SignupCode.objects.get(code=invite_token)
            candidate_user.signup_code = signup_code
            candidate_user.save()

        candidate_token = GenerateRandomString()

        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        from_email = Email(email="info@altsalt.com", name="AltSalt")
        to_email = To(email)

        sign_up_url = '{0}/user/verify-account'.format(os.environ.get('BASE_URL'))
        redeem_url = (sign_up_url + '?email={0}&token={1}').format(email, candidate_token)
        subject = 'Verify your AltSalt account'

        mail = Mail(from_email, to_email, subject)
        mail.dynamic_template_data = {
            'subject': subject,
            'title': 'Welcome to AltSalt',
            'message': 'Hi there! To finish setting up your AltSalt account, please click the button below.',
            'button_text': 'Verify Account',
            'sign_up_url': sign_up_url,
            'redeem_url': redeem_url,
            'token': candidate_token
        }
        mail.template_id = 'd-171f495feafe4472b043d3de1233b998'
        response = sg.client.mail.send.post(request_body=mail.get())

        candidate_user.candidate_token = make_password(candidate_token)
        candidate_user.save()

        return CreateCandidateUser(email=email)


def verify_candidate_user_mutate_wrapper(f):
    @wraps(f)
    @setup_jwt_cookie
    @csrf_rotation
    @refresh_expiration
    def wrapper(cls, root, info, **kwargs):
        email = kwargs.get('email')
        token = kwargs.get('token')

        if get_user_model().objects.filter(email=email, is_candidate=True).exists():

            user = get_user_model().objects.get(email=email, is_candidate=True)

            encrypted_token = user.candidate_token
            if check_password(token, encrypted_token) is True:

                user.is_candidate = False
                try:
                    send_welcome_email(user, False)
                except:
                    pass
                user.save()

                context = info.context
                context._jwt_token_auth = True

                if hasattr(context, 'user'):
                    context.user = user

                result = f(cls, root, info, **kwargs)
                signals.token_issued.send(sender=cls, request=context, user=user)
                return maybe_thenable((context, user, result), on_token_auth_resolve)
            else:
                raise GraphQLError("Token is invalid. Did you type the code in correctly?")
        else:
            raise GraphQLError("User verification failed.")

    return wrapper


class VerifyCandidateUser(ResolveMixin, JSONWebTokenMixin, graphene.Mutation):

    class Arguments:
        email = graphene.String(required=True)
        token = graphene.String(required=True)

    @classmethod
    # @ratelimit(group="create_user", key="ip", rate="5/hr",
    #            message="Max number of requests reached. Your device has been temporarily restricted."
    #                    " Please try again later.")
    @check_csrf
    @verify_candidate_user_mutate_wrapper
    def mutate(cls, root, info, **kwargs):
        return cls.resolve(root, info, **kwargs)


################################
# UPDATE NOTIFICATION SETTINGS #
################################


class UpdateNotificationSettings(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        frequency = graphene.String(required=True)
        user_id = graphene.String()
        request_id = graphene.String()
        token = graphene.String()

    @classmethod
    @ratelimit(group="update_notification_settings", key="ip", rate="30/hr",
               message="Max number of requests reached. Your device has been temporarily restricted."
                       " Please try again later.")
    @check_csrf
    def mutate(cls, self, info, **kwargs):

        notification_settings = None

        if info.context.user.is_authenticated is True:
            notification_settings = NotificationSettings.objects.get(user=info.context.user)

        else:
            user_id = kwargs.get('user_id')
            request_id = kwargs.get('request_id')
            token = kwargs.get('token')

            if user_id is not None and request_id is not None and token is not None and\
               NotificationSettingsAuthorizedUpdate.objects.filter(user_id=user_id, id=request_id).exists():
                    authorized_update = NotificationSettingsAuthorizedUpdate.objects.get(user_id=user_id, id=request_id)
                    encrypted_token = authorized_update.token
                    if check_password(token, encrypted_token) is True:
                        notification_settings = NotificationSettings.objects.get(user_id=user_id)

        frequency = kwargs.get('frequency')

        if notification_settings is not None:
            notification_settings.frequency = frequency
            notification_settings.save()
            return UpdateNotificationSettings(user=notification_settings.user)


##################
# RESET PASSWORD #
##################


def ResetPasswordRequestValid(email, token):

    if get_user_model().objects.filter(email=email).exists() is False:
        return False

    user = get_user_model().objects.get(email=email)

    reset_password_request = ResetPasswordRequest.objects.get(user=user)

    if reset_password_request is None:
        return False

    encrypted_token = reset_password_request.token
    if check_password(token, encrypted_token) is True:
        return True

    return False


class CreateResetPasswordRequest(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)

    @classmethod
    @ratelimit(group="reset_password_request", key="ip", rate="5/hr",
               message="Max number of requests reached. Your device has been temporarily restricted."
                       " Please try again later.")
    @check_csrf
    def mutate(cls, self, info, email):

        if get_user_model().objects.filter(email=email).exists() is True:

            user = get_user_model().objects.get(email=email)

            if ResetPasswordRequest.objects.filter(user=user).exists() is True:
                previous_request = ResetPasswordRequest.objects.get(user=user)
                previous_request.delete()

            token = GenerateRandomString()

            sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

            from_email = Email(email="info@altsalt.com", name="AltSalt")
            to_email = To(email)
            subject = "Reset your AltSalt password"
            mail = Mail(from_email, to_email, subject)
            mail.dynamic_template_data = {
                'email': email,
                'username': user.username,
                'url': '{0}/user/reset-password?email={1}&token={2}'.format(os.environ.get('BASE_URL'), email, token)
            }
            mail.template_id = 'd-3960424af31e4833a731bb3a7003e83f'
            response = sg.client.mail.send.post(request_body=mail.get())

            new_request = ResetPasswordRequest(user=user, token=make_password(token))
            new_request.save()

        return CreateResetPasswordRequest(success=True)


class VerifyResetPasswordRequest(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)
        token = graphene.String(required=True)

    @classmethod
    @ratelimit(group="verify_reset_password", key="ip", rate="5/hr",
               message="Max number of attempts reached. Your device has been temporarily restricted."
                       " Please try again later.")
    @check_csrf
    def mutate(cls, self, info, email, token):

        if ResetPasswordRequestValid(email, token) is True:
            return VerifyResetPasswordRequest(success=True)

        return VerifyResetPasswordRequest(success=False)


class ResetPassword(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)
        token = graphene.String(required=True)
        password = graphene.String(required=True)

    @classmethod
    @check_csrf
    def mutate(cls, self, info, email, token, password):

        if ResetPasswordRequestValid(email, token) is False:
            raise GraphQLError('Reset password request is invalid')

        else:
            user = get_user_model().objects.get(email=email)
            user.set_password(password)
            user.save()

            request = ResetPasswordRequest.objects.get(user=user)
            request.delete()

            logins = RefreshToken.objects.filter(user=user)
            for i in logins:
                i.delete()

            return ResetPassword(success=True)


############
# FEEDBACK #
############

class SendFeedback(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        subject = graphene.String(required=True)
        message = graphene.String(required=True)

    @classmethod
    @ratelimit(group="send_feedback", key="ip", rate="5/d",
               message="Max number of messages sent. Your device has been temporarily restricted."
                       " You can try Discord, or emailing us at info@altsalt.com.")
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        subject = kwargs.get('subject')
        message = kwargs.get('message')

        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

        # CONFIRMATION

        from_confirmation_email = Email(email="info@altsalt.com", name="AltSalt")
        to_confirmation_email = To(info.context.user.email)
        confirmation_email = Mail(from_confirmation_email, to_confirmation_email, subject)
        confirmation_email.dynamic_template_data = {
            'sender_email': info.context.user.email,
            'sender_username': info.context.user.username,
            'subject': subject,
            'message': message,
        }
        confirmation_email.template_id = 'd-ab2fd8f0ec8c4edc8e58accd466cefa9'
        confirmation_response = sg.client.mail.send.post(request_body=confirmation_email.get())

        # FEEDBACK

        from_feedback_email = Email(email=info.context.user.email, name=info.context.user.username)
        to_feedback_email = To('info@altsalt.com')

        feedback_email = Mail(from_feedback_email, to_feedback_email, subject)
        feedback_email.dynamic_template_data = {
            'sender_email': info.context.user.email,
            'sender_username': info.context.user.username,
            'subject': subject,
            'message': message,
        }
        feedback_email.template_id = 'd-547f4ba836a04abc8d4ba16c835bb19d'
        feedback_response = sg.client.mail.send.post(request_body=feedback_email.get())

        return SendFeedback(success=True)


###################
# SEND NEWSLETTER #
###################

class SendNewsletter(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        subject = graphene.String(required=True)
        preview_text = graphene.String(required=True)
        is_test = graphene.Boolean(required=True)
        category = graphene.String()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        if info.context.user.is_superuser is False:
            raise GraphQLError("You are not authorized to perform this action")

        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

        from_confirmation_email = Email(email="artemio@altsalt.com", name="AltSalt")
        subject = kwargs.get('subject')
        preview_text = kwargs.get('preview_text')
        is_test = kwargs.get('is_test')
        category = kwargs.get('category')

        all_users = User.objects.all()
        for user in all_users:
            notification_settings = NotificationSettings.objects.get(user=user)

            if notification_settings.frequency == notification_settings.Frequency.OFF:
                continue

            token = GenerateRandomString()
            notification_settings_authorized_update = NotificationSettingsAuthorizedUpdate(user=user,
                                                                                         token=make_password(token))
            notification_settings_authorized_update.save()

            notifications = Notification.objects.filter(recipient=user, is_read=False)
            notification_string = 'No notifications yet. We have a few publications on AltSalt; if you have a moment, ' \
                                  'you can try exercising your reciprocity muscle by resonating on a publication ' \
                                  '(like the one above) and spreading some good vibes!'
            if notifications.count() > 0:
                notification_string = 'You have {0} unread notifications:<br><br>'.format(notifications.count())
                for notification in notifications:
                    message = notification.get_simple_message()
                    notification_string += "• {0}<br>".format(message)
                notification_string += '<br>If you have a moment, ' \
                                       'you can try exercising your reciprocity muscle by ' \
                                       'checking out the above (or another publication) and ' \
                                       'spreading some good vibes!'

            email_preferences_url = "{0}/user/email-preferences?id={1}&requestId={2}&token={3}".format(
                os.environ.get('BASE_URL'), user.id, notification_settings_authorized_update.id, token)
            unsubscribe_url = "{0}&frequency={1}".format(email_preferences_url, notification_settings.Frequency.OFF)

            if is_test:
                to_confirmation_email = To("artemio@altsalt.com")
            else:
                to_confirmation_email = To(user.email)

            newsletter_email = Mail(from_confirmation_email, to_confirmation_email, subject)
            newsletter_email.dynamic_template_data = {
                "subject": subject,
                "preview_text": preview_text,
                "notifications": notification_string,
                "login_url": '{0}/user/login'.format(os.environ.get('BASE_URL')),
                "email_preferences_url": email_preferences_url,
                "unsubscribe_url": unsubscribe_url,
            }
            if category is not None:
                if is_test:
                    newsletter_email.category = Category("{0} Test {1}".format(category, os.environ.get('BASE_URL')))
                else:
                    newsletter_email.category = Category("{0} {1}".format(category, os.environ.get('BASE_URL')))

            newsletter_email.template_id = 'd-ff20f481a8d8470484706736e3f86a54'
            newsletter_response = sg.client.mail.send.post(request_body=newsletter_email.get())

        return SendNewsletter(success=True)


######################
# SEND WELCOME EMAIL #
######################

class SendWelcomeEmail(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        email = graphene.String(required=True)
        is_test = graphene.Boolean(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        if info.context.user.is_superuser is False:
            raise GraphQLError("You are not authorized to perform this action")

        email = kwargs.get('email')
        is_test = kwargs.get('is_test')

        if is_test:
            return send_welcome_email(info.context.user, is_test)

        else:
            if get_user_model().objects.filter(email=email).exists() is False:
                raise GraphQLError("Target user does not exist")

            user = get_user_model().objects.get(email=email)
            return send_welcome_email(user, is_test)

#####################
# SEND DIGEST EMAIL #
#####################


class SendDigestEmail(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        emails = graphene.List(graphene.String)
        is_test = graphene.Boolean(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        if info.context.user.is_superuser is False:
            raise GraphQLError("You are not authorized to perform this action")

        emails = kwargs.get('emails')
        is_test = kwargs.get('is_test')

        return send_digest_email(emails, is_test)


#######################
# JWT / REFRESH TOKEN #
#######################

class CustomVerifyToken(graphql_jwt.Verify):

    @classmethod
    @check_csrf
    def mutate(cls, root, info, **kwargs):
        return cls.verify(root, info, **kwargs)


class CustomRefreshToken(graphql_jwt.Refresh):

    @classmethod
    @check_csrf
    def mutate(cls, *args, **kwargs):
        return CustomRefreshToken.refresh(*args, **kwargs)


class CustomRevokeToken(graphql_jwt.Revoke):

    @classmethod
    @check_csrf
    def mutate(cls, *args, **kwargs):
        return CustomRevokeToken.revoke(*args, **kwargs)



##########
# SCHEMA #
##########


class UserQuery(graphene.ObjectType):
    me = graphene.Field(UserType)
    all_users = graphene.List(UserType)
    user = graphene.Field(UserType, username=graphene.String(), id=graphene.String())

    def resolve_me(self, info):
        authuser = info.context.user
        if not authuser.is_authenticated:
            raise Exception('Not logged in!')

        return authuser

    def resolve_all_users(self, info):
        return get_user_model().objects.all()

    def resolve_user(self, info, **kwargs):

        username = kwargs.get('username')
        id = kwargs.get('id')

        if username is not None and get_user_model().objects.filter(username=username).exists():
            return get_user_model().objects.get(username=username)

        if id is not None and get_user_model().objects.filter(id=int(id)).exists():
            return get_user_model().objects.get(id=int(id))

        return None


class UserMutation(graphene.ObjectType):
    create_full_user = CreateFullUser.Field()
    create_candidate_user = CreateCandidateUser.Field()
    verify_candidate_user = VerifyCandidateUser.Field()
    update_user = UpdateUser.Field()
    update_notifications = UpdateNotifications.Field()
    update_notification_settings = UpdateNotificationSettings.Field()
    confirm_byline = ConfirmByline.Field()
    confirm_membership = ConfirmMembership.Field()
    log_in = LogIn.Field()
    verify_token = CustomVerifyToken.Field()
    refresh_token = CustomRefreshToken.Field()
    revoke_token = CustomRevokeToken.Field()
    send_invitation = SendInvitation.Field()
    verify_user_creation_code = VerifyUserCreationCode.Field()
    send_newsletter = SendNewsletter.Field()
    send_welcome_email = SendWelcomeEmail.Field()
    send_digest_email = SendDigestEmail.Field()
    create_reset_password_request = CreateResetPasswordRequest.Field()
    verify_reset_password_request = VerifyResetPasswordRequest.Field()
    reset_password = ResetPassword.Field()
    send_feedback = SendFeedback.Field()
