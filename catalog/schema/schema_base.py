from catalog.models import Culture
from graphene_django.types import DjangoObjectType


class CultureType(DjangoObjectType):
    class Meta:
        model = Culture
