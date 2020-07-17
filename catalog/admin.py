from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django_reverse_admin import ReverseModelAdmin


    # fieldsets = [
    #     (None,  {'fields': ['question_text']}),
    #     ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    # inlines = [ChoiceInLine]
    # list_display = ('question_text', 'pub_date', 'was_published_recently')
    # list_filter = ['pub_date']
    # search_fields = ['question_text']

class ListingInline(admin.TabularInline):
    extra = 1
    pass


class ListingCoverImageInline(ListingInline):
    model = ListingCoverImage
    pass


class ListingPreviewImageInline(ListingInline):
    model = ListingPreviewImage
    pass


class ListingCreationBylineInline(ListingInline):
    model = ListingCreationByline
    pass


class ListingCollaboratorBylineInline(ListingInline):
    model = ListingCollaboratorByline
    pass


class CustomUserAdmin(UserAdmin):
    model = User

    fieldsets = UserAdmin.fieldsets + ((None,
            {'fields':
                (
                    'display_name',
                    'image',
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
    inline_reverse = ['listing_creation_bylines', 'listing_collaborator_bylines']
    inlines = [ListingCreationBylineInline, ListingCollaboratorBylineInline]


class ListingFormatInline(ListingInline):
    model = ListingFormat
    pass


class ListingDistributionTypeInline(ListingInline):
    model = ListingDistributionType
    pass


class ListingGenreInline(ListingInline):
    model = ListingGenre
    pass


class ListingLanguageInline(ListingInline):
    model = ListingLanguage
    pass


@admin.register(Listing)
class ListingAdmin(ReverseModelAdmin):
    inline_type = 'tabular'
    inline_reverse = ['preview_images']
    inlines = [ListingCoverImageInline,
               ListingPreviewImageInline,
               ListingCreationBylineInline,
               ListingCollaboratorBylineInline,
               ListingFormatInline,
               ListingDistributionTypeInline,
               ListingGenreInline,
               ListingLanguageInline]
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


admin.site.register(User, CustomUserAdmin)
