import graphene
from graphene_django.types import DjangoObjectType
from catalog.models.cms import Article, ArticleByline, ArticleFeaturedImage, EditorialSettings
from .schema_base import BaseImageTypeMixin


class ArticleBylineType(DjangoObjectType):
    class Meta:
        model = ArticleByline


class ArticleFeaturedImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = ArticleFeaturedImage


class EditorialSettingsType(DjangoObjectType):
    class Meta:
        model = EditorialSettings


class ArticleType(DjangoObjectType):
    bylines = graphene.List(ArticleBylineType)
    featured_image = graphene.Field(ArticleFeaturedImageType)

    class Meta:
        model = Article
        fields = ('id', 'title', 'slug', 'preview_text', 'featured_image', 'body', 'post_script',
                  'is_published', 'is_announcement', 'is_featured', 'is_full_bleed',)

    def resolve_bylines(self, info):
        return ArticleByline.objects.filter(article_id=self.id)

    def resolve_featured_image(self, info):
        if ArticleFeaturedImage.objects.filter(article=self).exists():
            return ArticleFeaturedImage.objects.get(article=self)
        else:
            return None


class CMSQuery(graphene.ObjectType):
    article_bundle = graphene.List(ArticleType)
    article = graphene.Field(ArticleType, id=graphene.String())
    editorial_settings = graphene.Field(EditorialSettingsType)

    def resolve_article_bundle(self, info):
        return Article.objects.filter(is_published=True)

    def resolve_article(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Article.objects.get(id=int(id))

        return None

    def resolve_editorial_settings(self, info):
        return EditorialSettings.objects.first()
