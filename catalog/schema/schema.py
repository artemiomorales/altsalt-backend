import graphene
from .schema_base import BaseQuery, BaseMutation
from .schema_listing import ListingQuery, ListingMutation
from .schema_user import UserQuery, UserMutation
from .schema_cms import CMSQuery, CMSMutation
from .schema_submission import SubmissionQuery, SubmissionMutation


class Query(BaseQuery, ListingQuery, UserQuery, CMSQuery, SubmissionQuery, graphene.ObjectType):
    pass


class Mutation(BaseMutation, ListingMutation, UserMutation, CMSMutation, SubmissionMutation, graphene.ObjectType):
    pass
