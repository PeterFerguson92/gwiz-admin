# Create your models here.
import uuid
from django.contrib import admin
from django_resized import ResizedImageField
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

s3_storage = S3Boto3Storage()


from homepage.upload import (
    about_us_homepage_upload_image1_path,
    about_us_homepage_upload_image2_path,
    about_us_section_upload_image1_path,
    about_us_section_upload_image2_path,
    homepage_logo_upload_image_path,
    homepage_slide1_upload_image_path,
    homepage_slide2_upload_image_path,
    homepage_slide3_upload_image_path,
)


# Register your models here.
class Banner(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    logo = ResizedImageField(
        "Logo",
        upload_to=homepage_logo_upload_image_path,
        quality=90,
        storage=s3_storage,  # ✅ force S3
    )

    img_slide_1 = ResizedImageField(
        "Image slide 1",
        size=[1342, 768],
        upload_to=homepage_slide1_upload_image_path,
        quality=90,
        storage=s3_storage,  # ✅ force S3
    )

    title_slide_1 = models.TextField("Title 1")
    subtitle_slide_1 = models.TextField("Subtitle 1")

    img_slide_2 = ResizedImageField(
        "Image slide 2",
        size=[1342, 768],
        upload_to=homepage_slide2_upload_image_path,
        quality=90,
        blank=True,
        null=True,
        storage=s3_storage,  # ✅ force S3
    )

    title_slide_2 = models.TextField("Title 2", blank=True, null=True)
    subtitle_slide_2 = models.TextField("Subtitle 2", blank=True, null=True)

    img_slide_3 = ResizedImageField(
        "Image slide 3",
        size=[1342, 768],
        upload_to=homepage_slide3_upload_image_path,
        quality=90,
        blank=True,
        null=True,
        storage=s3_storage,  # ✅ already here
    )

    title_slide_3 = models.TextField("Title 3", blank=True, null=True)
    subtitle_slide_3 = models.TextField("Subtitle 3", blank=True, null=True)

    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("title_slide_1", "created_at")
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __str__(self):
        return f"{self.title_slide_1}"


class AboutUs(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("Title", max_length=255, default="About Us")
    homepage_display_header = models.TextField("Homepage Display Header")
    homepage_display_text = models.TextField("Homepage Display Text")
    highlight_text1 = models.TextField("Highlight 1", blank=True, null=True)
    highlight_text2 = models.TextField("Highlight 2", blank=True, null=True)
    highlight_text3 = models.TextField("Highlight 3", blank=True, null=True)
    about_us_homepage_image1 = ResizedImageField(
        "About Us Homepage Image 1",
        upload_to=about_us_homepage_upload_image1_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    about_us_homepage_image2 = ResizedImageField(
        "About Us Homepage Image 2",
        size=[371, 421],
        upload_to=about_us_homepage_upload_image2_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    section_display_header = models.TextField(
        "Section Display Title", blank=True, null=True
    )
    section_display_text = models.TextField(
        "Section Display Text", blank=True, null=True
    )
    about_us_section_image1 = ResizedImageField(
        "About Us Section Image 1",
        upload_to=about_us_section_upload_image1_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    about_us_section_image2 = ResizedImageField(
        "About Us Section Image 2",
        size=[371, 421],
        upload_to=about_us_section_upload_image2_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "About Us"
        verbose_name_plural = "About Us"

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.id}"


class Homepage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("Title", max_length=255, default="Homepage")
    banner = models.ManyToManyField(to=Banner, blank=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Homepage"
        verbose_name_plural = "Homepage"

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.id}"
