from datetime import date
from django.conf import settings
from django.contrib.auth import get_user_model
from catalog.models import *

import graphene
from graphene_django.types import DjangoObjectType
from .schema_base import CultureType
from .schema_listing import ListingCreatorBylineType
from .schema_image import ImageType


def resolve_me(info):
    user = info.context.user
    if user.is_anonymous:
        raise Exception('Not logged in!')

    return user


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

    listing_creation_bylines = graphene.List(ListingCreatorBylineType)
    culture = graphene.List(UserCultureType)
    age = graphene.Int()
    links = graphene.List(UserLinkType)
    date_joined = graphene.String()

    def resolve_listing_creation_bylines(self, info):
        return ListingCreatorByline.objects.filter(user_id=self.id)

    def resolve_culture(self, info):
        return UserCulture.objects.filter(user_id=self.id)

    def resolve_profile_image(self, info):
        return self.profile_image.url

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
        userProfile = UserProfile(user=user)
        userProfile.save()

        return CreateUser(user=user)


class UserMutation(graphene.ObjectType):
    create_user = CreateUser.Field()
