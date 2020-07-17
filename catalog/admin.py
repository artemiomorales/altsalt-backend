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

class ListingCoverImageInline(admin.TabularInline):
    model = ListingCoverImage
    pass


class ListingPreviewImageInline(admin.TabularInline):
    model = ListingPreviewImage
    pass


class ListingCreationBylineInline(admin.TabularInline):
    model = ListingCreationByline
    pass


class ListingCollaboratorBylineInline(admin.TabularInline):
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


class ListingAdmin(ReverseModelAdmin):
    inline_type = 'tabular'
    inline_reverse = ['preview_images']
    inlines = [ListingCoverImageInline,
               ListingPreviewImageInline,
               ListingCreationBylineInline,
               ListingCollaboratorBylineInline]
    pass


class ImageAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, CustomUserAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(Image, ImageAdmin)
