
# Create your models here.
import uuid
from django.contrib import admin
from django_resized import ResizedImageField
from django.db import models

from homepage.upload import homepage_logo_upload_image_path



# Register your models here.
class Banner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_slide_1 = models.TextField("Title 1", blank=False, null=False)
    subtitle_slide_1 = models.TextField("Subtitle 1", blank=False, null=False)
    title_slide_2 = models.TextField("Title 2", blank=False, null=False)
    subtitle_slide_2 = models.TextField("Subtitle 2", blank=False, null=False)
    logo = ResizedImageField( "Logo",
        size=[133, 40],
        upload_to=homepage_logo_upload_image_path,
        quality=90
    )
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