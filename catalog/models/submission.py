from .base import TABLE_PREFIX, Link
from django.db import models
from django.utils import timezone
from catalog.backends import CatalogImageStorage, ThumbnailImageStorage
from catalog.constants import DEFAULT_FILE_UPLOAD_NAME
from .listing import Listing
from .user import User
from .base import submission_upload_path, Price


class Submission(models.Model):
    title = models.CharField(max_length=100)
    price = models.ForeignKey("Price", null=True, blank=True, on_delete=models.SET_NULL)
    date_submitted = models.DateField(default=timezone.now)
    is_approved = models.BooleanField(default=False)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(storage=CatalogImageStorage(default_acl='private'), upload_to=submission_upload_path, null=True, blank=True)
    additional_info = models.TextField(default="", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = TABLE_PREFIX + 'submission'


class SubmissionLink(Link):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)

    class Meta(Link.Meta):
        abstract = True


class SubmissionAvailabilityLink(SubmissionLink):

    class Meta(SubmissionLink.Meta):
        db_table = TABLE_PREFIX + 'submission_availability_link'


class SubmissionAdditionalLink(SubmissionLink):

    class Meta(SubmissionLink.Meta):
        db_table = TABLE_PREFIX + 'submission_additional_link'
