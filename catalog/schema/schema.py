import graphene
from .schema_base import BaseQuery, BaseMutation
from .schema_art import ArtQuery
from .schema_movie import MovieQuery
from .schema_listing import ListingQuery, ListingMutation
from .schema_user import UserQuery, UserMutation
from .schema_cms import CMSQuery, CMSMutation
from .schema_submission import SubmissionQuery, SubmissionMutation
from .schema_comments import CommentsMutation
from .schema_collection import CollectionQuery
from .schema_playlist import PlaylistQuery
from .schema_project import ProjectQuery


class Query(BaseQuery, ArtQuery, MovieQuery, ListingQuery, UserQuery, CMSQuery,
            SubmissionQuery, CollectionQuery, PlaylistQuery, ProjectQuery, graphene.ObjectType):
    pass


class Mutation(BaseMutation, ListingMutation, UserMutation, CMSMutation,
               SubmissionMutation, CommentsMutation, graphene.ObjectType):
    pass
