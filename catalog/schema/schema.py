import graphene
from .schema_listing import ListingQuery
from .schema_image import ImageQuery
from .schema_user import UserQuery, UserMutation
from .schema_cms import CMSQuery


class Query(ListingQuery, ImageQuery, UserQuery, CMSQuery, graphene.ObjectType):
    pass


class Mutation(UserMutation, graphene.ObjectType):
    pass
