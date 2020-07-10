from django.contrib.auth import get_user_model
from catalog.models import UserProfile, Listing, Image

import graphene
from graphene_django.types import DjangoObjectType


class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()


class ListingType(DjangoObjectType):
    class Meta:
        model = Listing


class ImageType(DjangoObjectType):
    class Meta:
        model = Image


def resolve_me(info):
    user = info.context.user
    if user.is_anonymous:
        raise Exception('Not logged in!')

    return user


class Query(object):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)
    listings = graphene.List(ListingType)
    image = graphene.Field(ImageType, id=graphene.Int())

    def resolve_users(self, info):
        return get_user_model().objects.all()

    def resolve_listings(self, info):
        return Listing.objects.all()

    def resolve_image(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Image.objects.get(id=id)

        return None;


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


class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
