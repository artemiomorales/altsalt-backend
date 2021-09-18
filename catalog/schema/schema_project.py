import graphene
from catalog.models.project import *
from .schema_base import BaseImageTypeMixin, GenericImageType, LinkType
from .schema_user import UserType
from .schema_collection import CollectionType
from graphene_django.types import DjangoObjectType
from django.template.defaultfilters import slugify


class ProjectCollectionType(DjangoObjectType):

    class Meta:
        model = ProjectCollection
        exclude = ('collection',)

    item = graphene.Field(CollectionType)

    def resolve_item(self, info):
        return Collection.objects.get(id=self.collection_id)


class ProjectType(DjangoObjectType):
    slug = graphene.String()
    # cover_image = graphene.Field(ProjectCoverImageType)
    collections = graphene.List(ProjectCollectionType)
    #
    def resolve_slug(self, info):
        return slugify(self.__str__())

    def resolve_collections(self, info):
        return ProjectCollection.objects.filter(project_id=self.id)

    class Meta:
        model = Project


class ProjectQuery(graphene.ObjectType):
    project = graphene.Field(ProjectType, id=graphene.String())
    project_bundle = graphene.List(ProjectType)

    def resolve_project(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Project.objects.get(id=int(id))

        return None

    def resolve_project_bundle(self, info, **kwargs):
        # include_featured = kwargs.get('include_featured')
        # exclude_private = kwargs.get('exclude_private')
        # approved_after_date = kwargs.get('approved_after_date')
        # approved_before_date = kwargs.get('approved_before_date')
        #
        # if include_featured is True:
        #     listings = Listing.objects.all()
        # else:
        #     listings = Listing.objects.filter(is_featured=False)
        #
        # if exclude_private is True:
        #     listings = listings.filter(is_published=True, is_approved=True)
        #
        # if approved_after_date is not None:
        #     listings = listings.filter(date_approved__gte=approved_after_date)
        #
        # if approved_before_date is not None:
        #     listings = listings.filter(date_approved__lt=approved_before_date)

        return Project.objects.all()