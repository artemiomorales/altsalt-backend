import graphene
from catalog.models.art import *
from django.contrib.auth import get_user_model
from catalog.models.base import ContentThread
from graphene_django.types import DjangoObjectType
from .schema_base import BaseImageTypeMixin, IdentityType, TagType, \
    GenreType, CountryType, PriceGrapheneType, ContentRatingType, \
    TextChoicesType, NameSlugType
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from catalog.models.user import UserCountry, UserIdentity


class ArtBylineType(DjangoObjectType):
    class Meta:
        model = ArtByline


class ArtUploadType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = ArtUpload


class ArtTagType(DjangoObjectType):
    class Meta:
        model = ArtTag
        exclude = ('tag',)

    item = graphene.Field(TagType)

    def resolve_item(self, info):
        return Tag.objects.get(id=self.tag_id)


class ArtGenreType(DjangoObjectType):
    class Meta:
        model = ArtGenre
        exclude = ('genre',)

    item = graphene.Field(GenreType)

    def resolve_item(self, info):
        return Genre.objects.get(id=self.genre_id)


class ArtCountryRepresentedType(DjangoObjectType):
    class Meta:
        model = ArtCountryRepresented
        exclude = ('country',)

    item = graphene.Field(CountryType)

    def resolve_item(self, info):
        return Country.objects.get(id=self.country_id)


class ArtIdentityRepresentedType(DjangoObjectType):
    class Meta:
        model = ArtIdentityRepresented
        exclude = ('identity',)

    item = graphene.Field(IdentityType)

    def resolve_item(self, info):
        return Identity.objects.get(id=self.identity_id)


class ArtType(DjangoObjectType):
    class Meta:
        model = Art
        fields = ('id', 'title', 'description', 'is_featured', 'hide_bylines', 'show_custom_author',
                  'custom_author', 'seo_title', 'content_rating')

    slug = graphene.String()
    uploads = graphene.List(ArtUploadType)
    genre_set = graphene.List(ArtGenreType)
    countries_represented = graphene.List(ArtCountryRepresentedType)
    identities_represented = graphene.List(ArtIdentityRepresentedType)
    tag_set = graphene.List(ArtTagType)
    moderator_authentication = graphene.Boolean()
    thread_set = graphene.List('catalog.schema.schema_comments.ContentThreadType')
    publish_status = graphene.Field(TextChoicesType)
    content_rating = graphene.Field(ContentRatingType)
    confirmed_creators = graphene.List('catalog.schema.schema_user.UserType')
    pending_creators = graphene.List('catalog.schema.schema_user.UserType')
    creator_background = graphene.List(NameSlugType)

    def resolve_slug(self, info):
        return slugify(self.title)

    def resolve_uploads(self, info):
        if ArtUpload.objects.filter(art=self).exists():
            return ArtUpload.objects.filter(art=self)
        else:
            return None

    def resolve_genre_set(self, info):
        return ArtGenre.objects.filter(art_id=self.id)

    def resolve_countries_represented(self, info):
        return ArtCountryRepresented.objects.filter(art_id=self.id)

    def resolve_identities_represented(self, info):
        return ArtIdentityRepresented.objects.filter(art_id=self.id)

    def resolve_tag_set(self, info):
        return ArtTag.objects.filter(art_id=self.id)

    def resolve_thread_set(self, info):
        return ContentThread.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(Art))

    def resolve_moderator_authentication(self, info):
        if info.context.user.is_authenticated is True and info.context.user.is_moderator is True:
            return True
        return False

    def resolve_publish_status(self, info):
        return {'value': PublishStatus(self.publish_status).value, 'label': PublishStatus(self.publish_status).label}

    def resolve_creator_background(self, info):
        users = []
        backgrounds = []

        creatorBylines = ArtByline.objects.filter(art_id=self.id).order_by('art_priority')
        for creatorByline in creatorBylines:
            users.extend(get_user_model().objects.filter(id=creatorByline.user.id))

        for user in users:

            user_countries = UserCountry.objects.filter(user_id=user.id)
            for user_country in user_countries:
                backgrounds.append({'name': user_country.country.name, 'slug': user_country.country.slug})
            user_identities = UserIdentity.objects.filter(user_id=user.id)
            for user_identity in user_identities:
                backgrounds.append({'name': user_identity.identity.name, 'slug': user_identity.identity.slug})

        remove_duplicates = []
        for i in backgrounds:
            if i not in remove_duplicates:
                remove_duplicates.append(i)

        return remove_duplicates

    def resolve_confirmed_creators(self, info):
        users = []

        creatorBylines = ArtByline.objects.filter(art_id=self.id).order_by('art_priority')
        for creatorByline in creatorBylines:
            if creatorByline.is_confirmed:
                users.append(creatorByline.user)

        if len(users) > 0:
            return users

        return None

    def resolve_pending_creators(self, info):
        is_authorized = False
        if info.context.user.is_authenticated and \
           (ArtByline.objects.filter(user=info.context.user).exists() or \
           ArtByline.objects.filter(user=info.context.user).exists()):
                is_authorized = True

        if not is_authorized:
            return None

        users = []
        creatorBylines = ArtByline.objects.filter(art_id=self.id).order_by('art_priority')
        for creatorByline in creatorBylines:
            if not creatorByline.is_confirmed:
                users.append(creatorByline.user)

        if len(users) > 0:
            return users

        return None



##########
# SCHEMA #
##########

class ArtQuery(graphene.ObjectType):
    featured_art = graphene.List(ArtType)
    art_bundle = graphene.List(ArtType,
                                   exclude_featured=graphene.Boolean(default_value=False),
                                   exclude_unlisted=graphene.Boolean(default_value=True),
                                   exclude_drafts=graphene.Boolean(default_value=True),
                                   )
    art = graphene.Field(ArtType, id=graphene.String())

    def resolve_featured_art(self, info, **kwargs):
        return Art.objects.filter(is_featured=True)

    def resolve_art_bundle(self, info, **kwargs):
        exclude_featured = kwargs.get('exclude_featured')
        exclude_unlisted = kwargs.get('exclude_unlisted')
        exclude_drafts = kwargs.get('exclude_drafts')

        if not exclude_featured:
            art = Art.objects.all()
        else:
            art = Art.objects.filter(is_featured=False)

        if exclude_unlisted is True:
            art = art.exclude(publish_status=PublishStatus.UNLISTED)

        if exclude_drafts is True:
            art = art.exclude(publish_status=PublishStatus.DRAFT)

        return art

    def resolve_art(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Art.objects.get(id=int(id))

        return None