import graphene
from graphene_django.types import DjangoObjectType
from catalog.models import *


class ArticleBylineType(DjangoObjectType):
    class Meta:
        model = ArticleByline


class ArticleType(DjangoObjectType):
    bylines = graphene.List(ArticleBylineType)

    def resolve_bylines(self, info):
        return ArticleByline.objects.filter(article_id=self.id)

    class Meta:
        model = Article
        fields = ('id', 'title', 'slug', 'preview_text', 'featured_image', 'body',)


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
