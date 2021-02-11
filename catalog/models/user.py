from .base import PROJECT_PREFIX, TABLE_PREFIX, profile_image_path, Country, Identity, CustomImage, Link, media_upload_path

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.utils.translation import gettext, gettext_lazy as _
from catalog.backends import ThumbnailImageStorage


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)
    display_name = models.CharField(max_length=150, blank=True)
    short_name = models.CharField(max_length=18, blank=True)
    description = models.TextField(default="", blank=True)
    location = models.CharField(max_length=50, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    show_age = models.BooleanField(default=False)
    is_organization = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    country = models.ManyToManyField(
        "Country",
        through='UserCountry'
    )
    identity = models.ManyToManyField(
        "Identity",
        through='UserIdentity'
    )

    listing_creator_bylines = models.ManyToManyField(
        "Listing",
        through='ListingCreatorByline',
        related_name="creatorBylines",
        through_fields=('user', 'listing'),
    )

    listing_collaborator_bylines = models.ManyToManyField(
        "Listing",
        through='ListingCollaboratorByline',
        related_name="collaboratorBylines",
        through_fields=('user', 'listing'),
    )

    article_bylines = models.ManyToManyField(
        "Article",
        through='ArticleByline',
        related_name="articleBylines"
    )

    members = models.ManyToManyField(
        "User",
        through='OrganizationMember'
    )

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so display name
            self.display_name = self.first_name + ' ' + self.last_name

        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.username

    class Meta:
        db_table = PROJECT_PREFIX + 'user'


class UserProfileImage(CustomImage):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=600, target_height=600),
                                 upload_to=profile_image_path, null=True, blank=True)

    large = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=137, target_height=137),
                              upload_to=profile_image_path, null=True, blank=True)

    medium = models.ImageField(storage=
                               ThumbnailImageStorage(target_width=112, target_height=112),
                               upload_to=profile_image_path, null=True, blank=True)

    small = models.ImageField(storage=
                              ThumbnailImageStorage(target_width=40, target_height=40),
                              upload_to=profile_image_path, null=True, blank=True)

    class Meta:
        db_table = PROJECT_PREFIX + 'user_profile_image'


class UserLink(Link):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta(Link.Meta):
        db_table = TABLE_PREFIX + 'user_link'


class UserCountry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'user_country'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['user', 'country'], name='user_country_link')
        ]


class UserIdentity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    identity = models.ForeignKey(Identity, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'user_identity'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['user', 'identity'], name='user_identity_link')
        ]


class OrganizationMember(models.Model):
    organization = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member')
    is_admin = models.BooleanField(default=False)
    is_confirmed = models.BooleanField(default=False)
    organization_priority = models.IntegerField(default=0)
    member_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'organization_member'
        constraints = [
            models.CheckConstraint(check=~Q(organization_id=models.F("member_id")), name='prevent_self_reference'),
            models.UniqueConstraint(fields=['organization_id', 'member_id'], name='organization_member_link')
        ]


class Invitation(models.Model):
    email = models.CharField(max_length=120)
    token = models.CharField(max_length=120)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    redeemed = models.BooleanField(default=False)

    def __str__(self):
        if getattr(self, 'requester') is not None:
            return self.requester.username
        return '-'

    class Meta:
        db_table = TABLE_PREFIX + 'invitation'
        constraints = [
            models.UniqueConstraint(fields=['email', 'token'], name='email_token_pair')
        ]


class ResetPasswordRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=120)

    class Meta:
        db_table = TABLE_PREFIX + 'reset_password_request'
        constraints = [
            models.UniqueConstraint(fields=['user', 'token'], name='user_token_pair')
        ]
