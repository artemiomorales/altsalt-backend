from .base import \
    TABLE_PREFIX, PublishStatus, CustomImageAlttext, project_cover_image_path
from django.db import models
from catalog.models.collection import Collection
from catalog.backends import ThumbnailImageStorage


class Project(models.Model):
    title1 = models.CharField(default="", max_length=100, blank=False)
    title2 = models.CharField(default="", max_length=100, blank=True)
    description = models.TextField(default="", blank=True)
    postscript = models.TextField(default="", blank=True)

    publish_status = models.CharField(
        max_length=2,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )

    def __str__(self):
        return "{0} {1}".format(self.title1, self.title2)

    class Meta:
        db_table = TABLE_PREFIX + 'project'


class ProjectCoverImage(CustomImageAlttext):
    project = models.OneToOneField(
        "Project",
        on_delete=models.CASCADE,
        null=True
    )

    original = models.ImageField(storage=
                                 ThumbnailImageStorage(target_width=1588, target_height=2382),
                                 upload_to=project_cover_image_path, null=True, blank=True)

    class Meta:
        db_table = TABLE_PREFIX + 'project_cover_image'


class ProjectCollection(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        db_table = TABLE_PREFIX + 'project_collection'
        ordering = ['priority']
        constraints = [
            models.UniqueConstraint(fields=['project', 'collection'], name='project_collection_link')
        ]