from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
from catalog.models import *

import graphene
import graphql_jwt
from graphene_django.types import DjangoObjectType
from .schema_base import CultureType
from .schema_listing import ListingCreatorBylineType, ListingCollaboratorBylineType
from .schema_image import ImageType
from .schema_cms import ArticleBylineType
from django.contrib.auth import authenticate


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
        print(info.context.user)
        user = info.context.user
        if user.is_anonymous:
            raise Exception('Not logged in!')

        return user

    def resolve_users(self, info):
        return get_user_model().objects.all()

    def resolve_user(self, info, **kwargs):

        username = kwargs.get('username')

        if username is not None:
            return get_user_model().objects.get(username=username)

        return None


class CreateUser(graphene.Mutation):
    user = graphene.Field(UserType)

    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        date_of_birth = graphene.types.datetime.Date(required=True)

    def mutate(self, info, email, username, password, date_of_birth):
        user = get_user_model()(
            username=username,
            email=email,
            date_of_birth=date_of_birth
        )
        user.set_password(password)
        user.save()

        return CreateUser(user=user)

    def resolve_user(self, info):
        return User.objects.get()

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
