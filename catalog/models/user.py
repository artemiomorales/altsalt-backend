from .base import PROJECT_PREFIX, TABLE_PREFIX

from .base import profile_directory_path, listing_directory_path
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to=profile_directory_path, blank=True)
    description = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=50, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    occupation = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(blank=True)
    is_organization = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    listing_creation_bylines = models.ManyToManyField(
        "Listing",
        through='ListingCreationByline',
        related_name="creationBylines"
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


