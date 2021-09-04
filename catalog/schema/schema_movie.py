import graphene
from catalog.models.movie import *
from django.contrib.auth import get_user_model
from catalog.models.base import ContentThread
from graphene_django.types import DjangoObjectType
from .schema_base import BaseImageTypeMixin, IdentityType, TagType, \
    GenreType, CountryType, PriceGrapheneType, ContentRatingType, \
    TextChoicesType, NameSlugType
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify
from catalog.models.user import UserCountry, UserIdentity


class MovieBylineType(DjangoObjectType):
    class Meta:
        model = MovieByline


class MovieCoverImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = MovieCoverImage


class MovieTagType(DjangoObjectType):
    class Meta:
        model = MovieTag
        exclude = ('tag',)

    item = graphene.Field(TagType)

    def resolve_item(self, info):
        return Tag.objects.get(id=self.tag_id)


class MovieGenreType(DjangoObjectType):
    class Meta:
        model = MovieGenre
        exclude = ('genre',)

    item = graphene.Field(GenreType)

    def resolve_item(self, info):
        return Genre.objects.get(id=self.genre_id)


class MovieCountryRepresentedType(DjangoObjectType):
    class Meta:
        model = MovieCountryRepresented
        exclude = ('country',)

    item = graphene.Field(CountryType)

    def resolve_item(self, info):
        return Country.objects.get(id=self.country_id)


class MovieIdentityRepresentedType(DjangoObjectType):
    class Meta:
        model = MovieIdentityRepresented
        exclude = ('identity',)

    item = graphene.Field(IdentityType)

    def resolve_item(self, info):
        return Identity.objects.get(id=self.identity_id)


# Generic type for extracting video information when needed
class VideoType(graphene.ObjectType):
    id = graphene.String()
    src_1080 = graphene.String()
    src_720 = graphene.String()
    src_360 = graphene.String()
    width = graphene.Int()
    height = graphene.Int()
    cover_image = graphene.Field(MovieCoverImageType)

class MovieType(DjangoObjectType):
    class Meta:
        model = Movie
        fields = ('id', 'title', 'description', 'is_featured', 'seo_title', 'content_rating',
                  'src_1080', 'src_720', 'src_360', 'width', 'height', 'playtime')

    slug = graphene.String()
    cover_image = graphene.Field(MovieCoverImageType)
    genre_set = graphene.List(MovieGenreType)
    countries_represented = graphene.List(MovieCountryRepresentedType)
    identities_represented = graphene.List(MovieIdentityRepresentedType)
    tag_set = graphene.List(MovieTagType)
    moderator_authentication = graphene.Boolean()
    thread_set = graphene.List('catalog.schema.schema_comments.ContentThreadType')
    publish_status = graphene.Field(TextChoicesType)
    content_rating = graphene.Field(ContentRatingType)
    confirmed_creators = graphene.List('catalog.schema.schema_user.UserType')
    pending_creators = graphene.List('catalog.schema.schema_user.UserType')
    creator_background = graphene.List(NameSlugType)

    def resolve_slug(self, info):
        return slugify(self.title)

    def resolve_cover_image(self, info):
        if MovieCoverImage.objects.filter(movie=self).exists():
            return MovieCoverImage.objects.get(movie=self)
        else:
            return None

    def resolve_genre_set(self, info):
        return MovieGenre.objects.filter(movie_id=self.id)

    def resolve_countries_represented(self, info):
        return MovieCountryRepresented.objects.filter(movie_id=self.id)

    def resolve_identities_represented(self, info):
        return MovieIdentityRepresented.objects.filter(movie_id=self.id)

    def resolve_tag_set(self, info):
        return MovieTag.objects.filter(movie_id=self.id)

    def resolve_thread_set(self, info):
        return ContentThread.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(Movie))

    def resolve_moderator_authentication(self, info):
        if info.context.user.is_authenticated is True and info.context.user.is_moderator is True:
            return True
        return False

    def resolve_publish_status(self, info):
        return {'value': PublishStatus(self.publish_status).value, 'label': PublishStatus(self.publish_status).label}

    def resolve_creator_background(self, info):
        users = []
        backgrounds = []

        creatorBylines = MovieByline.objects.filter(movie_id=self.id).order_by('movie_priority')
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

        creatorBylines = MovieByline.objects.filter(movie_id=self.id).order_by('movie_priority')
        for creatorByline in creatorBylines:
            if creatorByline.is_confirmed:
                users.append(creatorByline.user)

        if len(users) > 0:
            return users

        return None

    def resolve_pending_creators(self, info):
        is_authorized = False
        if info.context.user.is_authenticated and \
           (MovieByline.objects.filter(user=info.context.user).exists() or \
           MovieByline.objects.filter(user=info.context.user).exists()):
                is_authorized = True

        if not is_authorized:
            return None

        users = []
        creatorBylines = MovieByline.objects.filter(movie_id=self.id).order_by('movie_priority')
        for creatorByline in creatorBylines:
            if not creatorByline.is_confirmed:
                users.append(creatorByline.user)

        if len(users) > 0:
            return users

        return None



##########
# SCHEMA #
##########

class MovieQuery(graphene.ObjectType):
    featured_movie = graphene.List(MovieType)
    movie_bundle = graphene.List(MovieType,
                                   exclude_featured=graphene.Boolean(default_value=False),
                                   exclude_unlisted=graphene.Boolean(default_value=True),
                                   exclude_drafts=graphene.Boolean(default_value=True),
                                   )
    movie = graphene.Field(MovieType, id=graphene.String())

    def resolve_featured_movie(self, info, **kwargs):
        return Movie.objects.filter(is_featured=True)

    def resolve_movie_bundle(self, info, **kwargs):
        exclude_featured = kwargs.get('exclude_featured')
        exclude_unlisted = kwargs.get('exclude_unlisted')
        exclude_drafts = kwargs.get('exclude_drafts')

        if not exclude_featured:
            movie = Movie.objects.all()
        else:
            movie = Movie.objects.filter(is_featured=False)

        if exclude_unlisted is True:
            movie = movie.exclude(publish_status=PublishStatus.UNLISTED)

        if exclude_drafts is True:
            movie = movie.exclude(publish_status=PublishStatus.DRAFT)

        return movie

    def resolve_movie(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Movie.objects.get(id=int(id))

        return None