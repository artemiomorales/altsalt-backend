from catalog.models.base import Comment, Thread, Notification
from catalog.models.listing import Listing
from catalog.models.cms import Article, ArticleByline
from .schema_base import check_csrf, ThreadType
from .schema_listing import ListingType, ListingCreatorByline, ListingCollaboratorByline
from .schema_cms import ArticleType

from catalog.models.base import ContentThread
from django.contrib.contenttypes.models import ContentType
from graphql_jwt.decorators import login_required
from graphql import GraphQLError

import graphene
from graphene_django.types import DjangoObjectType


class ContentThreadType(DjangoObjectType):
    class Meta:
        model = ContentThread
        exclude = ('thread',)

    item = graphene.Field(ThreadType)

    def resolve_item(self, info):
        return Thread.objects.get(id=self.thread_id)


class CreateContentThread(graphene.Mutation):
    listing = graphene.Field(ListingType)
    article = graphene.Field(ArticleType)

    class Arguments:
        content_id = graphene.String(required=True)
        content_type = graphene.String(required=True)
        body = graphene.String(required=True)

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        content_id = kwargs.get('content_id')
        content_type = kwargs.get('content_type')
        body = kwargs.get('body')

        if content_type != 'listing' and content_type != 'article':
            raise GraphQLError("Content type not recognized")

        target_type = ContentType.objects.get(app_label='catalog', model=content_type)
        target_model = target_type.model_class()

        if target_model.objects.filter(id=content_id).exists() is False:
            raise GraphQLError("Target object does not exist! Please refresh or try again later.")

        target_object = target_model.objects.get(id=content_id)

        if body.strip() == '':
            raise GraphQLError("Comment body must not be empty")

        new_thread = Thread(originator=info.context.user)
        new_thread.save()

        new_content_thread = ContentThread(content_type=target_type, object_id=content_id, thread=new_thread)
        new_content_thread.save()

        new_comment = Comment(thread=new_thread, commenter=info.context.user, body=body, is_root=True)
        new_comment.save()

        # Create notifications

        if content_type == 'listing':

            creator_bylines = ListingCreatorByline.objects.filter(listing=target_object)
            for creator_byline in creator_bylines:
                if info.context.user != creator_byline.user:
                    notification = Notification(content_object=new_content_thread, notifier=info.context.user,
                                                recipient=creator_byline.user)
                    notification.save()

            collaborator_bylines = ListingCollaboratorByline.objects.filter(listing=target_object)
            for collaborator_byline in collaborator_bylines:
                if info.context.user != collaborator_byline.user:
                    notification = Notification(content_object=new_content_thread, notifier=info.context.user,
                                                recipient=collaborator_byline.user)
                    notification.save()

            return CreateContentThread(listing=target_object, article=None)

        if content_type == 'article':

            author_bylines = ArticleByline.objects.filter(article=target_object)
            for author_byline in author_bylines:
                if info.context.user != author_byline.user:
                    notification = Notification(content_object=new_content_thread, notifier=info.context.user,
                                                recipient=author_byline.user)
                    notification.save()

            return CreateContentThread(article=target_object, listing=None)


class CreateContentThreadReply(graphene.Mutation):
    listing = graphene.Field(ListingType)
    article = graphene.Field(ArticleType)

    class Arguments:
        content_id = graphene.String(required=True)
        content_type = graphene.String(required=True)
        thread = graphene.String(required=True)
        body = graphene.String()

    @classmethod
    @check_csrf
    @login_required
    def mutate(cls, self, info, **kwargs):

        content_id = kwargs.get('content_id')
        content_type = kwargs.get('content_type')
        thread = kwargs.get('thread')
        body = kwargs.get('body')

        if content_type != 'listing' and content_type != 'article':
            raise GraphQLError("Content type not recognized")

        target_type = ContentType.objects.get(app_label='catalog', model=content_type)
        target_model = target_type.model_class()

        if target_model.objects.filter(id=content_id).exists() is False:
            raise GraphQLError("Target object does not exist! Please refresh or try again later.")

        if Thread.objects.filter(id=thread).exists() is False:
            raise GraphQLError("Target thread does not exist! Please refresh or try again later")

        target_content_object = target_model.objects.get(id=content_id)
        target_thread = Thread.objects.get(id=thread)

        can_reply = False

        if target_thread.originator == info.context.user:
            can_reply = True

        if content_type == 'listing':
            if can_reply is False:
                creator_bylines = ListingCreatorByline.objects.filter(listing=target_content_object)
                for creator_byline in creator_bylines:
                    if creator_byline.user == info.context.user:
                        can_reply = True
                        break

            if can_reply is False:
                collaborator_bylines = ListingCollaboratorByline.objects.filter(listing=target_content_object)
                for collaborator_byline in collaborator_bylines:
                    if collaborator_byline.user == info.context.user:
                        can_reply = True
                        break

        if content_type == 'article':
            if can_reply is False:
                author_bylines = ArticleByline.objects.filter(article=target_content_object)
                for author_byline in author_bylines:
                    if author_byline.user == info.context.user:
                        can_reply = True
                        break

        if can_reply is False:
            raise GraphQLError("Only original posters, creators, and collaborators may reply to threads")

        if body.strip() == '':
            raise GraphQLError("Comment body must not be empty")

        new_comment = Comment(thread=target_thread, commenter=info.context.user, body=body, is_root=False)
        new_comment.save()

        # Create notifications
        thread_comments = Comment.objects.filter(thread=target_thread)
        thread_subscribers = []
        for thread_comment in thread_comments:
            if info.context.user != thread_comment.commenter and thread_comment.commenter not in thread_subscribers:
                thread_subscribers.append(thread_comment.commenter)

        for subscriber in thread_subscribers:
            notification = Notification(content_object=new_comment, notifier=info.context.user,
                                        recipient=subscriber)
            notification.save()

        if content_type == 'listing':
            return CreateContentThreadReply(listing=target_content_object, article=None)
        elif content_type == 'article':
            return CreateContentThreadReply(listing=None, article=target_content_object)


class CommentsMutation(graphene.ObjectType):
    create_content_thread = CreateContentThread.Field()
    create_content_thread_reply = CreateContentThreadReply.Field()