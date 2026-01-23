# Create your models here.
import os
import uuid

from django.contrib import admin
from django.db import models
from django_resized import ResizedImageField
from storages.backends.s3boto3 import S3Boto3Storage

s3_storage = S3Boto3Storage()


def get_google_oauth_client_id():
    return os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")


from homepage.upload import (
    about_us_cover_upload_image_path,
    about_us_homepage_upload_image1_path,
    about_us_homepage_upload_image2_path,
    about_us_section_upload_image1_path,
    about_us_section_upload_image2_path,
    assets_cancel_cover_upload_image_path,
    assets_contact_us_cover_upload_image_path,
    assets_login_cover_upload_image_path,
    assets_main_classes_cover_upload_image_path,
    assets_main_events_cover_upload_image_path,
    assets_personal_area_cover_upload_image_path,
    assets_personal_bookings_cover_upload_image_path,
    assets_personal_tickets_cover_upload_image_path,
    contact_background_upload_image_path,
    footer_logo_upload_image_path,
    homepage_logo_upload_image_path,
    homepage_slide1_upload_image_path,
    homepage_slide2_upload_image_path,
    homepage_slide3_upload_image_path,
    service_cover_upload_image_path,
    team_trainer_profile_upload_image_path,
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


class Trainer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_image = ResizedImageField(
        "Profile Image",
        upload_to=team_trainer_profile_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )

    name = models.CharField("Name", max_length=255)
    role = models.CharField("Role", max_length=255)
    instagram_link = models.CharField(
        "Instagram Link", max_length=255, blank=True, null=True
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Trainer"
        verbose_name_plural = "Trainers"

    def __str__(self):
        return self.name


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("Title", max_length=255, default="Team")
    header = models.CharField("Header", max_length=255, default="Meet our Trainers")
    description = models.TextField("Description", blank=True, null=True)
    trainers = models.ManyToManyField(to=Trainer, blank=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "Team"
        verbose_name_plural = "Team"

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValueError("Only one Team instance is allowed.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.title}"


class AboutUs(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField("Title", max_length=255, default="About Us")
    cover_image = ResizedImageField(
        "Cover Image",
        upload_to=about_us_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
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
    section_highlight_text1 = models.TextField(
        "Section Highlight 1", blank=True, null=True
    )
    section_highlight_text2 = models.TextField(
        "Section Highlight 2", blank=True, null=True
    )
    section_highlight_text3 = models.TextField(
        "Section Highlight 3", blank=True, null=True
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
    team = models.OneToOneField(Team, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "About Us"
        verbose_name_plural = "About Us"

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValueError("Only one AboutUs instance is allowed.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.title}"


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cover_image = ResizedImageField(
        "Cover Image",
        upload_to=service_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    name = models.CharField("name", max_length=255)
    short_description = models.TextField("Short Description")
    long_description = models.TextField("Long Description", blank=True, null=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("name", "created_at")
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.name}"


class Faq(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField("Question")
    answer = models.TextField("Answer")
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("question", "created_at")
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ's"

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.question}"


class Contact(models.Model):
    background_image = ResizedImageField(
        "Background Image",
        upload_to=contact_background_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    header = models.CharField("Header", max_length=255)
    description = models.TextField("Description", blank=True, null=True)
    phone = models.CharField("phone", max_length=255)
    address = models.CharField("Address", max_length=255)
    email = models.CharField("Email", max_length=255)
    social = models.CharField("Social", max_length=255)
    access_key = models.CharField("Access key", max_length=255)
    google_key = models.CharField(
        "Google key",
        max_length=255,
        default=get_google_oauth_client_id,
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("header", "created_at")
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValueError("Only one instance is allowed.")
        self.google_key = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        return super().save(*args, **kwargs)

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.header}"


class Footer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    logo = ResizedImageField(
        "logo",
        upload_to=footer_logo_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    slogan = models.TextField("Slogan", blank=True, null=True)
    contact = models.OneToOneField(
        Contact, on_delete=models.CASCADE, blank=True, null=True
    )
    services = models.ManyToManyField(to=Service, blank=True)
    instagram_link = models.CharField("Instagram Link", max_length=255)
    tiktok_link = models.CharField("Tik Tok Link", max_length=255)
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("id", "created_at")
        verbose_name = "Footer"
        verbose_name_plural = "Footers"

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValueError("Only one instance is allowed.")
        return super().save(*args, **kwargs)

    def __unicode__(self):
        return "%s: /n %s %s  %s %s" % (
            self.id,
            self.created_at,
        )

    def __str__(self):
        return f"{self.id}"


class Assets(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login_cover = ResizedImageField(
        "login cover",
        upload_to=assets_login_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    personal_area_cover = ResizedImageField(
        "Personal area cover",
        upload_to=assets_personal_area_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    main_events_cover = ResizedImageField(
        "Main events cover",
        upload_to=assets_main_events_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    main_classes_cover = ResizedImageField(
        "Main classes cover",
        upload_to=assets_main_classes_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    personal_tickets_cover = ResizedImageField(
        "Personal tickets cover",
        upload_to=assets_personal_tickets_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    personal_bookings_cover = ResizedImageField(
        "Personal bookings cover",
        upload_to=assets_personal_bookings_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    contact_us_cover = ResizedImageField(
        "Contact us cover",
        upload_to=assets_contact_us_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    cancel_cover = ResizedImageField(
        "Cancel cover",
        upload_to=assets_cancel_cover_upload_image_path,
        null=True,
        blank=True,
        storage=s3_storage,
    )
    created_at = models.DateTimeField("Created at", auto_now_add=True)

    class Meta:
        ordering = ("id", "created_at")
        verbose_name = "Assets"
        verbose_name_plural = "Assets"

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValueError("Only one instance is allowed.")
        return super().save(*args, **kwargs)

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
    banner = models.OneToOneField(
        Banner, on_delete=models.CASCADE, blank=True, null=True
    )
    about_us = models.OneToOneField(
        AboutUs, on_delete=models.CASCADE, blank=True, null=True
    )
    services = models.ManyToManyField(to=Service, blank=True)

    service_title = models.CharField(
        "Service Title", max_length=255, default="Our Services"
    )
    service_description = models.TextField("Service Description", blank=True, null=True)
    faq_title = models.CharField("FAQ Title", max_length=255, default="Our Faq")
    faq_description = models.TextField("FAQ Description", blank=True, null=True)
    faqs = models.ManyToManyField(to=Faq, blank=True)
    services = models.ManyToManyField(to=Service, blank=True)
    contact = models.OneToOneField(
        Contact, on_delete=models.CASCADE, blank=True, null=True
    )
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
