# Create your models here.
import uuid
from django.contrib import admin
from django_resized import ResizedImageField
from django.db import models

from homepage.upload import homepage_logo_upload_image_path


# Register your models here.
class Banner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    logo = ResizedImageField(
        "Logo",
        size=[133, 40],
        upload_to=homepage_logo_upload_image_path,
        quality=90,
    )
    img_slide_1 = ResizedImageField(
        "Image slide 1",
        size=[1342, 768],
        upload_to=homepage_logo_upload_image_path,
        quality=90
    )
    title_slide_1 = models.TextField("Title 1")
    subtitle_slide_1 = models.TextField("Subtitle 1")
    img_slide_2 = ResizedImageField(
        "Image slide 2",
        size=[1342, 768],
        upload_to=homepage_logo_upload_image_path,
        quality=90,
        blank=True,
        null=True,
    )
    title_slide_2 = models.TextField("Title 2", blank=False, null=False)
    subtitle_slide_2 = models.TextField("Subtitle 2", blank=False, null=False)
    img_slide_3 = ResizedImageField(
        "Image slide 3",
        size=[1342, 768],
        upload_to=homepage_logo_upload_image_path,
        quality=90,
        blank=True,
        null=True,
    )
    title_slide_3 = models.TextField("Title 3", blank=False, null=False)
    subtitle_slide_3 = models.TextField("Subtitle 3", blank=False, null=False)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("title_slide_1", "created_at")
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.title_slide_1,
            self.created_at,
        )

    def __str__(self):
        return f"{self.title_slide_1}"
