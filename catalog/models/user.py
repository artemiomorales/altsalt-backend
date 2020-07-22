from .base import PROJECT_PREFIX, TABLE_PREFIX, profile_image_path, media_upload_path, Culture

from .base import Link
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    profile_image = models.ImageField(upload_to=profile_image_path, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=50, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(blank=True)
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
