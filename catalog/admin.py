from django import forms
from django.contrib import admin
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.utils.translation import gettext, gettext_lazy as _

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

from catalog.models.user import *
from catalog.models.base import *
from catalog.models.listing import *
from catalog.models.cms import *
from catalog.models.submission import *


from django_reverse_admin import ReverseModelAdmin


class SingleInline(admin.TabularInline):
    extra = 1
    pass


class UserCountryInline(SingleInline):
    model = UserCountry
    pass


class UserIdentityInline(SingleInline):
    model = UserIdentity
    pass


class UserLinkInline(SingleInline):
    model = UserLink
    pass


class UserProfileImageInline(SingleInline):
    model = UserProfileImage
    fields = ('original',)
    pass


class ArticleFeaturedImageInline(SingleInline):
    model = ArticleFeaturedImage
    fields = ('original', 'alttext', 'caption')
    pass


class ListingCoverImageInline(SingleInline):
    model = ListingCoverImage
    fields = ('original', 'alttext')
    pass


class ListingPreviewImageInline(SingleInline):
    model = ListingPreviewImage
    fields = ('original', 'alttext', 'caption')
    pass


class ListingCreationBylineInlineForListing(SingleInline):
    model = ListingCreatorByline
    fk_name = 'listing'
    pass


class ListingCollaboratorBylineInlineForListing(SingleInline):
    model = ListingCollaboratorByline
    fk_name = 'listing'
    pass


class ListingCreationBylineInlineForUser(SingleInline):
    model = ListingCreatorByline
    fk_name = 'user'
    pass


class ListingCollaboratorBylineInlineForUser(SingleInline):
    model = ListingCollaboratorByline
    fk_name = 'user'
    pass


class RoleInline(SingleInline):
    model = OrganizationMember
    fk_name = "member"
    verbose_name = "Role"
    verbose_name_plural = "Roles"
    pass


class MemberInline(SingleInline):
    model = OrganizationMember
    fk_name = "organization"
    verbose_name = "Member"
    verbose_name_plural = "Members"
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
        (None, {'fields': ('username', 'password', 'email', 'first_name', 'last_name', 'is_moderator', 'is_verified')}),
        (_('Profile'), {'fields':
                            ('display_name',
                             'short_name',
                             'description',
                             'location',
                             'pronouns',
                             'occupation',
                             'date_of_birth',
                             'show_age',
                             )}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Organization Settings'), {
            'fields': ('is_organization',),
        }),
    )

    inline_type = 'tabular'
    inline_reverse = ['user_profile_image, listing_creation_bylines', 'listing_collaborator_bylines', 'user_culture', 'organization_member']
    inlines = [UserProfileImageInline, RoleInline, MemberInline, ListingCreationBylineInlineForUser, ListingCollaboratorBylineInlineForUser,
               UserCountryInline, UserIdentityInline, UserLinkInline]

    def get_inline_instances(self, request, obj=None):
        return obj and super(CustomUserAdmin, self).get_inline_instances(request, obj) or []


class ListingAvailabilityLinkInline(SingleInline):
    model = ListingAvailabilityLink
    pass


class ListingAdditionalLinkInline(SingleInline):
    model = ListingAdditionalLink
    pass


class PriceInline(SingleInline):
    model = Price
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


class ListingCountryRepresentedInline(SingleInline):
    model = ListingCountryRepresented
    pass


class ListingIdentityRepresentedInline(SingleInline):
    model = ListingIdentityRepresented
    pass


class ListingTagInline(SingleInline):
    model = ListingTag
    pass


class ListingUploadInline(SingleInline):
    model = ListingUpload
    pass

@admin.register(UserProfileImage)
class UserProfileImageAdmin(admin.ModelAdmin):
    pass


@admin.register(Listing)
class ListingAdmin(ReverseModelAdmin):
    inline_type = 'tabular'
    inline_reverse = ['price']
    inlines = [ListingCoverImageInline,
               ListingPreviewImageInline,
               ListingCreationBylineInlineForListing,
               ListingCollaboratorBylineInlineForListing,
               ListingUploadInline,
               ListingAvailabilityLinkInline,
               ListingAdditionalLinkInline,
               ListingFormatInline,
               ListingDistributionTypeInline,
               ListingGenreInline,
               ListingLanguageInline,
               ListingCountryRepresentedInline,
               ListingIdentityRepresentedInline,
               ListingTagInline
               ]
    pass


class SubmissionAvailabilityLinkInline(SingleInline):
    model = SubmissionAvailabilityLink
    pass


class SubmissionAdditionalLinkInline(SingleInline):
    model = SubmissionAdditionalLink
    pass


@admin.register(Submission)
class SubmissionAdmin(ReverseModelAdmin):
    inline_type = 'tabular'
    inline_reverse = ['listing', 'price']
    inlines = [
                SubmissionAvailabilityLinkInline,
                SubmissionAdditionalLinkInline,
               ]
    pass


class ArticleBylineInline(SingleInline):
    model = ArticleByline
    pass


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    inlines = [ArticleBylineInline, ArticleFeaturedImageInline]
    pass


@admin.register(Format)
class FormatAdmin(admin.ModelAdmin):
    pass


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'requester', 'redeemed')}),
    )
    pass


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    pass


@admin.register(PriceType)
class PriceTypeAdmin(admin.ModelAdmin):
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


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    pass


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    pass


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Continent)
class ContinentAdmin(admin.ModelAdmin):
    pass


@admin.register(ContentRating)
class ContentRatingAdmin(admin.ModelAdmin):
    pass


@admin.register(SeoCategory)
class SeoCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(EditorialSettings)
class EditorialSettingsAdmin(admin.ModelAdmin):
    pass


class CommentInline(SingleInline):
    model = Comment
    pass


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    inlines = [CommentInline,]
    pass


@admin.register(ListingThread)
class ListingThreadAdmin(admin.ModelAdmin):
    pass


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    pass


@admin.register(ReactionType)
class ReactionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    pass


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    pass
