from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from catalog.models.user import User
from catalog.models.image import *
from catalog.models.base import *
from catalog.models.listing import *

from django_reverse_admin import ReverseModelAdmin

    # fieldsets = [
    #     (None,  {'fields': ['question_text']}),
    #     ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    # inlines = [ChoiceInLine]
    # list_display = ('question_text', 'pub_date', 'was_published_recently')
    # list_filter = ['pub_date']
    # search_fields = ['question_text']


class SingleInline(admin.TabularInline):
    extra = 1
    pass


class UserCultureInline(SingleInline):
    model = UserCulture
    pass


class UserLinkInline(SingleInline):
    model = UserLink
    pass


class ListingCoverImageInline(SingleInline):
    model = ListingCoverImage
    pass


class ListingPreviewImageInline(SingleInline):
    model = ListingPreviewImage
    pass


class ListingCreationBylineInline(SingleInline):
    model = ListingCreatorByline
    pass


class ListingCollaboratorBylineInline(SingleInline):
    model = ListingCollaboratorByline
    pass


class ImageInline(SingleInline):
    model = Image
    pass


class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + ((None,
            {'fields':
                (
                    'display_name',
                    'profile_image',
                    'description',
                    'location',
                    'pronouns',
                    'occupation',
                    'date_of_birth',
                    'is_organization',
                    'is_banned',
                )
            }),
         )

    inline_type = 'tabular'
    inline_reverse = ['listing_creation_bylines', 'listing_collaborator_bylines', 'user_culture']
    inlines = [ListingCreationBylineInline, ListingCollaboratorBylineInline, UserCultureInline, UserLinkInline, ImageInline]


class ListingAvailabilityLinkInline(SingleInline):
    model = ListingAvailabilityLink
    pass


class ListingAdditionalLinkInline(SingleInline):
    model = ListingAdditionalLink
    pass


class ListingFormatInline(SingleInline):
    model = ListingFormat
    pass


class ListingDistributionTypeInline(SingleInline):
    model = ListingDistributionType
    pass


class ListingGenreInline(SingleInline):
    model = ListingGenre
    pass


class ListingLanguageInline(SingleInline):
    model = ListingLanguage
    pass


class ListingCultureRepresentedInline(SingleInline):
    model = ListingCultureRepresented
    pass


@admin.register(Listing)
class ListingAdmin(ReverseModelAdmin):
    inline_type = 'tabular'
    inline_reverse = ['preview_images']
    inlines = [ListingCoverImageInline,
               ListingPreviewImageInline,
               ListingCreationBylineInline,
               ListingCollaboratorBylineInline,
               ListingAvailabilityLinkInline,
               ListingAdditionalLinkInline,
               ListingFormatInline,
               ListingDistributionTypeInline,
               ListingGenreInline,
               ListingLanguageInline,
               ListingCultureRepresentedInline]
    pass


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    pass


@admin.register(DistributionType)
class DistributionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Length)
class LengthAdmin(admin.ModelAdmin):
    pass


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    pass


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


@admin.register(Culture)
class Culture(admin.ModelAdmin):
    pass


@admin.register(Continent)
class Continent(admin.ModelAdmin):
    pass


admin.site.register(User, CustomUserAdmin)
