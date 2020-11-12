import graphene
from .schema_listing import ListingQuery, ListingMutation
from .schema_user import UserQuery, UserMutation
from .schema_cms import CMSQuery


class Query(ListingQuery, UserQuery, CMSQuery, graphene.ObjectType):
    pass


class Mutation(ListingMutation, UserMutation, graphene.ObjectType):
    pass
