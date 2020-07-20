from django.conf import settings
from django.contrib.auth import get_user_model
from catalog.models import *

import graphene
from graphene_django.types import DjangoObjectType
from .schema_listing import ListingCreationBylineType


def resolve_me(info):
    user = info.context.user
    if user.is_anonymous:
        raise Exception('Not logged in!')

    return user


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()

    listing_creation_bylines = graphene.List(ListingCreationBylineType)

    def resolve_listing_creation_bylines(self, info):
        return ListingCreationByline.objects.filter(user_id=self.id)


class UserQuery(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    def resolve_users(self, info):
        return get_user_model().objects.all()


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
