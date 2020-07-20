import graphene
from .schema_listing import ListingQuery
from .schema_image import ImageQuery
from .schema_user import UserQuery, UserMutation


class Query(ListingQuery, ImageQuery, UserQuery, graphene.ObjectType):
    pass


class Mutation(UserMutation, graphene.ObjectType):
    pass
