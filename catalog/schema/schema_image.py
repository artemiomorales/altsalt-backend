from django.conf import settings
from django.contrib.auth import get_user_model
from catalog.models import *

import graphene
from graphene_django.types import DjangoObjectType


MEDIA_URL = settings.MEDIA_URL


class ImageType(DjangoObjectType):
    class Meta:
        model = Image

    storage_url = graphene.String()

    def resolve_storage_url(self, info):
        return f"{MEDIA_URL}{self.url}"


class ImageQuery(graphene.ObjectType):
    cover_image = graphene.Field(ImageType, listing_id=graphene.Int())
    image = graphene.Field(ImageType, id=graphene.Int())

    def resolve_cover_image(self, info, **kwargs):

        listing_id = kwargs.get('listing_id')

        if listing_id is not None:
            listingCoverImage = ListingCoverImage.objects.get(listing_id=listing_id)
            return Image.objects.get(id=listingCoverImage.image_id)

        return None

    def resolve_image(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Image.objects.get(id=id)

        return None