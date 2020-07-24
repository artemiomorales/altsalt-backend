from django import forms
from django.contrib import admin
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.utils.translation import gettext, gettext_lazy as _

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

from catalog.models.user import *
from catalog.models.image import *
from catalog.models.base import *
from catalog.models.listing import *

from django_reverse_admin import ReverseModelAdmin



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


class OrganizationMemberInline(SingleInline):
    model = OrganizationMember
    fk_name = "organization"
    pass

#
# class CustomUserCreateForm(forms.ModelForm):
#     password1 = forms.CharField(
#         label=_("Password"),
#         strip=False,
#         widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
#         help_text=password_validation.password_validators_help_text_html(),
#     )
#     password2 = forms.CharField(
#         label=_("Password confirmation"),
#         widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
#         strip=False,
#         help_text=_("Enter the same password as before, for verification."),
#     )



@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    add_fieldsets = UserAdmin.add_fieldsets + ((None,
            {'fields':
                (
                    'email',
                    'first_name',
                    'last_name',
                    'date_of_birth',
                )
            }),
         )

    fieldsets = (
        (None, {'fields': ('username', 'password', 'email', 'first_name', 'last_name')}),
        (_('Profile'), {'fields':
                            ('display_name',
                             'short_name',
                             'profile_image',
                             'description',
                             'location',
                             'pronouns',
                             'occupation',
                             'date_of_birth',
                             )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Organization Settings'), {
            'fields': ('is_organization',),
        }),
    )

    inline_type = 'tabular'
    inline_reverse = ['listing_creation_bylines', 'listing_collaborator_bylines', 'user_culture', 'organization_member']
    inlines = [ OrganizationMemberInline, ListingCreationBylineInline, ListingCollaboratorBylineInline,
               UserCultureInline, UserLinkInline, ImageInline]

    def get_inline_instances(self, request, obj=None):
        return obj and super(CustomUserAdmin, self).get_inline_instances(request, obj) or []


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