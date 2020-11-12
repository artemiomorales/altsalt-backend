import graphene
from graphene_django.types import DjangoObjectType
from catalog.models.cms import Article, ArticleByline, ArticleFeaturedImage
from .schema_base import BaseImageTypeMixin


class ArticleBylineType(DjangoObjectType):
    class Meta:
        model = ArticleByline


class ArticleFeaturedImageType(DjangoObjectType, BaseImageTypeMixin):
    class Meta:
        model = ArticleFeaturedImage


class ArticleType(DjangoObjectType):
    bylines = graphene.List(ArticleBylineType)
    featured_image = graphene.Field(ArticleFeaturedImageType)

    class Meta:
        model = Article
        fields = ('id', 'title', 'slug', 'preview_text', 'featured_image', 'body',)

    def resolve_bylines(self, info):
        return ArticleByline.objects.filter(article_id=self.id)

    def resolve_featured_image(self, info):
        if ArticleFeaturedImage.objects.filter(article=self).exists():
            return ArticleFeaturedImage.objects.get(article=self)
        else:
            return None


class CMSQuery(graphene.ObjectType):
    article_bundle = graphene.List(ArticleType)
    article = graphene.Field(ArticleType, slug=graphene.String())

    def resolve_article_bundle(self, info):
        return Article.objects.all()

    def resolve_article(self, info, **kwargs):
        slug = kwargs.get('slug')

        if slug is not None:
            return Article.objects.get(slug=slug)

        return None
