import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

PROJECT_PREFIX = settings.PROJECT_PREFIX
TABLE_PREFIX = 'catalog_'


class User(AbstractUser):
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()

    class Meta:
        db_table = PROJECT_PREFIX + 'user'


def profile_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'catalog/user_{0}/{1}'.format(instance.user, filename)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        primary_key=True,
        on_delete=models.CASCADE,
    )
    display_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to=profile_directory_path)
    description = models.CharField(max_length=255)
    location = models.CharField(max_length=50)
    pronouns = models.CharField(max_length=50)
    occupation = models.CharField(max_length=50)
    is_organization = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return User.objects.get(id=self.user.id).username

    class Meta:
        db_table = TABLE_PREFIX + 'user_profile'


class Listing(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField()
    preview_images = models.ManyToManyField(
        "Image",
        through='ListingPreviewImage'
    )
    publication_date = models.DateField()
    date_added = models.DateField()
    is_approved = models.BooleanField()
    is_published = models.BooleanField()

    # length_id = models.ForeignKey(
    #     'Length'
    # )
    # price_id = models.ForeignKey(
    #     'Price'
    # )

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'listing'


def listing_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    date = datetime.datetime.now()
    return 'catalog/images/{0}/{1}-{2}'. format(date.strftime("%m%d%y"), date.strftime("%f"), filename)


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, blank=True)
    url = models.ImageField(upload_to=listing_directory_path)
    caption = models.CharField(max_length=300, blank=True)
    alttext = models.CharField(max_length=300)

    def __str__(self):
        return self.url.__str__()

    class Meta:
        db_table = TABLE_PREFIX + 'image'


class ListingCoverImage(models.Model):
    listing = models.OneToOneField(
        Listing,
        primary_key=True,
        on_delete=models.CASCADE,
    )
    image = models.ForeignKey(Image, on_delete=models.CASCADE)

    class Meta:
        db_table = TABLE_PREFIX + 'listing_cover_image'


class ListingPreviewImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    priority = models.IntegerField()

    class Meta:
        db_table = TABLE_PREFIX + 'listing_preview_image'
        constraints = [
            models.UniqueConstraint(fields=['listing', 'image'], name='listing_preview_image_link')
        ]

    # class Length(models.Model);
#     length_id = models.AutoField(primary_key=True)
#     length_name = models.CharField(max_length=50)
#     length_slug = models.SlugField()
#
#     class Meta:
#         db_table = TABLE_PREFIX + 'length'

# def clean(self):
#     if self.user is None:
#         raise ValidationError(_('A user profile must be associated with a base user.'))
#
# def save(self, *args, **kwargs):
#     self.
#     super(UserProfile, self).save(*args, **kwargs)
