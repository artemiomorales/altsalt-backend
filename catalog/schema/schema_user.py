from datetime import date
from django.contrib.auth import get_user_model
from catalog.models.cms import *
from catalog.models.user import *
from catalog.models.listing import *

import graphene
from graphene_django.types import DjangoObjectType
from .schema_base import check_csrf, save_image_data, BaseImageTypeMixin, CultureType, LinkInput, \
    CultureInput, CreateCulture
from .schema_listing import ListingCreatorBylineType, ListingCollaboratorBylineType
from .schema_cms import ArticleBylineType
from django.contrib.auth.hashers import make_password, check_password
import os
import random
import string
from graphql import GraphQLError
from django.template.defaultfilters import slugify

# Image handling
import base64
import PIL.Image as ImageUtils
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


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

from datetime import datetime
import logging

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


class UserCultureType(DjangoObjectType):
    class Meta:
        model = UserCulture
        exclude = ('culture',)

    item = graphene.Field(CultureType)

    def resolve_item(self, info):
        return Culture.objects.get(id=self.culture_id)


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


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ('id', 'is_moderator', 'username', 'display_name', 'short_name', 'occupation',
                  'description', 'is_organization', 'date_of_birth', 'show_age', 'pronouns', 'location', 'date_joined')

    profile_image = graphene.Field(UserProfileImageType)
    listings = graphene.List(ListingCreatorBylineType)
    collaborations = graphene.List(ListingCollaboratorBylineType)
    articles = graphene.List(ArticleBylineType)
    culture = graphene.List(UserCultureType)
    age = graphene.Int()
    links = graphene.List(UserLinkType)
    date_joined = graphene.String()
    organizations = graphene.List(OrganizationMemberType)
    admins = graphene.List(OrganizationMemberType)
    members = graphene.List(OrganizationMemberType)

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

    def resolve_culture(self, info):
        return UserCulture.objects.filter(user_id=self.id)

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


#########
# UTILS #
#########


def GenerateRandomString():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(12))



##########
# LOG IN #
##########

class LogIn(graphql_jwt.ObtainJSONWebToken):
    user = graphene.Field(UserType)

    @classmethod
    @check_csrf
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)


###############
# UPDATE USER #
###############

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
        background = graphene.List(CultureInput)
        creator_bylines = graphene.List(UserBylineInput)
        collaborator_bylines = graphene.List(UserBylineInput)

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
        background = kwargs.get('background')
        creator_bylines = kwargs.get('creator_bylines')
        collaborator_bylines = kwargs.get('collaborator_bylines')

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

        existing_background = UserCulture.objects.filter(user=target_user)
        existing_background.delete()

        if background is not None:
            for culture in background:
                culture_slug = slugify(culture.name)
                if Culture.objects.filter(slug=culture_slug).exists() is False:
                    CreateCulture(culture.name, culture_slug, culture.continent)

                culture_object = Culture.objects.get(slug=culture_slug)
                user_culture = UserCulture(user=target_user, culture=culture_object, priority=culture.priority)
                user_culture.save()

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

        target_user.save()

        return UpdateUser(user=target_user)


####################
# ACCOUNT CREATION #
####################


def CreateAccountRequestValid(invite_email, invite_token):
    invitation = Invitation.objects.get(email=invite_email)

    if invitation is None:
        return False

    encrypted_token = invitation.token
    if check_password(invite_token, encrypted_token) is True:
        return True

    return False


class SendInvitation(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        invite_email = graphene.String(required=True)
        is_test = graphene.Boolean()
        subject = graphene.String()
        title = graphene.String()
        message = graphene.String()

    @classmethod
    @check_csrf
    def mutate(cls, self, info, **kwargs):

        if info.context.user.is_moderator is False:
            raise GraphQLError('You are not authorized to perform this action')

        invite_email = kwargs.get('invite_email')
        is_test = kwargs.get("is_test")

        if is_test is True:
            invite_email = info.context.user.email

        if get_user_model().objects.filter(email=invite_email).exists() is True and is_test is False:
            raise GraphQLError('User with specified email already exists!')

        if Invitation.objects.filter(email=invite_email).exists() is True and is_test is False:
            previous_invitation = Invitation.objects.get(email=invite_email)
            previous_invitation.delete()

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
        from_email = Email("info@altsalt.com")
        to_email = To(invite_email)

        sign_up_url = '{0}/user/signup'.format(os.environ.get('BASE_URL'));
        redeem_url = (sign_up_url + '?inviteEmail={0}&inviteToken={1}').format(invite_email, invite_token)

        mail = Mail(from_email, to_email, subject)
        mail.dynamic_template_data = {
            'subject': subject,
            'title': title,
            'message': message,
            'sign_up_url': sign_up_url,
            'redeem_url': redeem_url,
            'token': invite_token
        }
        mail.template_id = 'd-171f495feafe4472b043d3de1233b998'
        response = sg.client.mail.send.post(request_body=mail.get())

        if is_test:
            new_invitation = Invitation(email=invite_email, token=make_password(invite_token))
            return SendInvitation(success=True)

        else:
            new_invitation = Invitation(email=invite_email, token=make_password(invite_token))
            new_invitation.save()
            return SendInvitation(success=True)


class VerifyInvitation(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        invite_email = graphene.String(required=True)
        invite_token = graphene.String(required=True)

    @classmethod
    @check_csrf
    def mutate(cls, self, info, invite_email, invite_token):
        if CreateAccountRequestValid(invite_email, invite_token) is True:
            return VerifyInvitation(success=True)

        return VerifyInvitation(success=False)


def creation_user_mutate_wrapper(f):
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

        if CreateAccountRequestValid(invite_email, invite_token) is False:
            raise GraphQLError('Invitation is invalid')

        else:
            if get_user_model().objects.filter(username=username).exists() is True:
                raise GraphQLError('Username is not available')

            if get_user_model().objects.filter(email=invite_email).exists() is True:
                raise GraphQLError('User with specified email already exists')

            new_user = get_user_model()(
                first_name=first_name,
                last_name=last_name,
                display_name=first_name + ' ' + last_name,
                username=username,
                email=invite_email
            )
            new_user.set_password(password)
            new_user.save()

            invitation = Invitation.objects.get(email=invite_email)
            invitation.delete()

            context = info.context
            context._jwt_token_auth = True

            if hasattr(context, 'user'):
                context.user = new_user

            result = f(cls, root, info, **kwargs)
            signals.token_issued.send(sender=cls, request=context, user=new_user)
            return maybe_thenable((context, new_user, result), on_token_auth_resolve)

    return wrapper


class CreateUser(ResolveMixin, JSONWebTokenMixin, graphene.Mutation):

    class Arguments:
        invite_email = graphene.String(required=True)
        invite_token = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    @classmethod
    @check_csrf
    @creation_user_mutate_wrapper
    def mutate(cls, root, info, **kwargs):
        return cls.resolve(root, info, **kwargs)


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
    @check_csrf
    def mutate(cls, self, info, email):

        if get_user_model().objects.filter(email=email).exists() is True:

            user = get_user_model().objects.get(email=email)

            if ResetPasswordRequest.objects.filter(user=user).exists() is True:
                previous_request = ResetPasswordRequest.objects.get(user=user)
                previous_request.delete()

            token = GenerateRandomString()

            sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

            from_email = Email("info@altsalt.com")
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
    user = graphene.Field(UserType, username=graphene.String())

    def resolve_me(self, info):
        authuser = info.context.user
        if not authuser.is_authenticated:
            raise Exception('Not logged in!')

        return authuser

    def resolve_all_users(self, info):
        return get_user_model().objects.all()

    def resolve_user(self, info, **kwargs):

        username = kwargs.get('username')

        if username is not None:
            return get_user_model().objects.get(username=username)

        return None


class UserMutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    log_in = LogIn.Field()
    verify_token = CustomVerifyToken.Field()
    refresh_token = CustomRefreshToken.Field()
    revoke_token = CustomRevokeToken.Field()
    send_invitation = SendInvitation.Field()
    verify_invitation = VerifyInvitation.Field()
    create_reset_password_request = CreateResetPasswordRequest.Field()
    verify_reset_password_request = VerifyResetPasswordRequest.Field()
    reset_password = ResetPassword.Field()
