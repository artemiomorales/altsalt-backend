from calendar import timegm
from datetime import date, datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from catalog.models import *

import graphene
import graphql_jwt
from graphql_jwt.decorators import jwt_settings, rotate_token, signals, on_token_auth_resolve
from graphql_jwt.mixins import JSONWebTokenMixin
from graphene_django.types import DjangoObjectType
from .schema_base import CultureType
from .schema_listing import ListingCreatorBylineType, ListingCollaboratorBylineType
from .schema_image import ImageType
from .schema_cms import ArticleBylineType
from django.contrib.auth import authenticate
from django.core.management.utils import get_random_secret_key
from django.contrib.auth.hashers import make_password, check_password
import sendgrid
import os
import random
import string
from sendgrid.helpers.mail import *
from bs4 import BeautifulSoup
from graphql import GraphQLError


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


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ('id', 'profile_image', 'username', 'display_name', 'short_name', 'occupation',
                  'description', 'is_organization', 'show_age', 'pronouns', 'location', 'date_joined')

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
        if self.profile_image:
            return self.profile_image.url

        return None

    def resolve_age(self, info):
        born = self.date_of_birth
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def resolve_links(self, info):
        return UserLink.objects.filter(user_id=self.id)

    def resolve_date_joined(self, info):
        return self.date_joined.strftime("%m/%d/%y")


class UserQuery(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)
    user = graphene.Field(UserType, username=graphene.String())

    def resolve_me(self, info):
        authuser = info.context.user
        if not authuser.is_authenticated:
            raise Exception('Not logged in!')

        return authuser

    def resolve_users(self, info):
        return get_user_model().objects.all()

    def resolve_user(self, info, **kwargs):

        username = kwargs.get('username')

        if username is not None:
            return get_user_model().objects.get(username=username)

        return None


class CreateUser(JSONWebTokenMixin, graphene.Mutation):

    class Arguments:
        invite_email = graphene.String(required=True)
        invite_token = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        date_of_birth = graphene.Date(required=True)
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, **kwargs):
        invite_email = kwargs.get('invite_email')
        invite_token = kwargs.get('invite_token')
        username = kwargs.get('username')
        first_name = kwargs.get('first_name')
        last_name = kwargs.get('last_name')
        date_of_birth = kwargs.get('date_of_birth')
        password = kwargs.get('password')

        if InvitationValid(invite_email, invite_token) is False:
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
                email=invite_email,
                date_of_birth=date_of_birth
            )
            new_user.set_password(password)
            new_user.save()

            # Create auth token
            context = info.context
            context._jwt_token_auth = True
            signals.token_issued.send(sender=self, request=context, user=new_user)
            on_token_auth_resolve((context, new_user, context))

            # from graphql_jwt.decorators.token_auth
            info.context.jwt_token = context.token

            # from graphql_jwt.decorators.csrf_rotation
            if jwt_settings.JWT_CSRF_ROTATION:
                rotate_token(info.context)

            # from graphql_jwt.decorators.refresh_expiration
            context.payload['refresh_expires_in'] = (
                timegm(datetime.datetime.utcnow().utctimetuple()) +
                jwt_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()
            )

            context.payload['username'] = username

            # invitation = Invitation.objects.get(email=invite_email)
            # invitation.delete()

            return CreateUser(token=context.token, payload=context.payload)


class SendInvitation(graphene.Mutation):
    invitation = graphene.Field(InvitationType)

    class Arguments:
        invite_email = graphene.String(required=True)

    def mutate(self, info, invite_email):

        if get_user_model().objects.filter(email=invite_email).exists() is True:
            raise GraphQLError('User with specified email already exists!')

        if Invitation.objects.filter(email=invite_email).exists() is True:
            previous_invitation = Invitation.objects.get(email=invite_email)
            previous_invitation.delete()

        letters = string.ascii_lowercase
        invite_token = ''.join(random.choice(letters) for i in range(12))

        sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

        from_email = Email("info@altsalt.com")
        to_email = To(invite_email)
        subject = "Welcome to AltSalt!"
        html_template = """Hello, you have been invited to create an AltSalt account! Please visit
                    <a href='https://altsalt-frontend-ten.vercel.app/user/signup?inviteEmail={0}&inviteToken={1}'>the following URL</a> to
                    redeem your invitation. You may also visit https://altsalt-frontend-ten.vercel.app/signup and
                    manually input your email and the following invite code: {1}
                    """
        formatted_content = html_template.format(invite_email, invite_token)
        html_content = HtmlContent(formatted_content)
        soup = BeautifulSoup(formatted_content)
        plain_text = soup.getText()
        plain_text_content = Content("text/plain", plain_text)
        mail = Mail(from_email, to_email, subject, plain_text_content, html_content)
        response = sg.client.mail.send.post(request_body=mail.get())

        new_invitation = Invitation(email=invite_email, token=make_password(invite_token))
        new_invitation.save()

        return SendInvitation(invitation=new_invitation)


def InvitationValid(invite_email, invite_token):
    invitation = Invitation.objects.get(email=invite_email)

    if invitation is None:
        return False

    encrypted_token = invitation.token
    if check_password(invite_token, encrypted_token) is True:
        return True

    return False


class VerifyInvitation(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        invite_email = graphene.String(required=True)
        invite_token = graphene.String(required=True)

    def mutate(self, info, invite_email, invite_token):
        if InvitationValid(invite_email, invite_token) is True:
            return VerifyInvitation(success=True)

        return VerifyInvitation(success=False)

# class UserWebToken(graphql_jwt.ObtainJSONWebToken):
#     user = graphene.Field(UserType)
#
#     def resolve_user(self, info):
#         return get_user_model().objects.get(username=info.context.user)


class UserMutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    log_in = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    delete_token_cookie = graphql_jwt.DeleteJSONWebTokenCookie.Field()
    send_invitation = SendInvitation.Field()
    verify_invitation = VerifyInvitation.Field()

    # Long running refresh tokens
    #delete_refresh_token_cookie = graphql_jwt.DeleteRefreshTokenCookie.Field()
