from .base import PROJECT_PREFIX, TABLE_PREFIX, profile_image_path, media_upload_path, Culture

from .base import Link


from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.utils.translation import gettext, gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)
    display_name = models.CharField(max_length=150, blank=True)
    short_name = models.CharField(max_length=18, blank=True)
    profile_image = models.ImageField(upload_to=profile_image_path, null=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=50, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True)
    show_age = models.BooleanField(default=False)
    is_organization = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    culture = models.ManyToManyField(
        "Culture",
        through='UserCulture'
    )

    listing_creator_bylines = models.ManyToManyField(
        "Listing",
        through='ListingCreatorByline',
        related_name="creatorBylines"
    )

    listing_collaborator_bylines = models.ManyToManyField(
        "Listing",
        through='ListingCollaboratorByline',
        related_name="collaboratorBylines"
    )

    article_bylines = models.ManyToManyField(
        "Article",
        through='ArticleByline',
        related_name="articleBylines"
    )

    members = models.ManyToManyField(
        "User",
        through='OrganizationMember',
        related_name="collaboratorBylines"
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


class UserLink(Link):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta(Link.Meta):
        db_table = TABLE_PREFIX + 'user_link'


class UserCulture(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    culture = models.ForeignKey(Culture, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'user_culture'
        ordering = ['-priority']
        constraints = [
            models.UniqueConstraint(fields=['user', 'culture'], name='user_culture_link')
        ]


class OrganizationMember(models.Model):
    organization = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization')
    member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='member')
    is_admin = models.BooleanField(default=False)
    organization_priority = models.IntegerField(default=0)
    member_priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'organization_member'
        constraints = [
            models.CheckConstraint(check=~Q(organization_id=models.F("member_id")), name='prevent_self_reference'),
            models.UniqueConstraint(fields=['organization_id', 'member_id'], name='organization_member_link')
        ]