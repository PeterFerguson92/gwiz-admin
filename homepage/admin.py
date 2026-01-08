from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from homepage.models import (
    AboutUs,
    Assets,
    Banner,
    Contact,
    Faq,
    Footer,
    Homepage,
    Service,
    Team,
    Trainer,
)


@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    search_fields = ("title_slide_1__startswith",)

    list_display = (
        "title_slide_1",
        "title_slide_2",
        "title_slide_3",
        "created_at",
    )

    readonly_fields = [
        "created_at",
    ]

    fieldsets = [
        (
            "Logo",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("logo",),
            },
        ),
        (
            "Slide 1",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    "img_slide_1",
                    ("title_slide_1", "subtitle_slide_1"),
                ),
            },
        ),
        (
            "Slide 2",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    "img_slide_2",
                    ("title_slide_2", "subtitle_slide_2"),
                ),
            },
        ),
        (
            "Slide 3",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    "img_slide_3",
                    ("title_slide_3", "subtitle_slide_3"),
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]

    unfold_fieldsets_in_tabs = True


@admin.register(AboutUs)
class AboutUsAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    readonly_fields = ("created_at",)

    fieldsets = [
        (
            "General",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("title", "cover_image", "team"),
            },
        ),
        (
            "Homepage Display",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    "homepage_display_header",
                    "homepage_display_text",
                    "highlight_text1",
                    "highlight_text2",
                    "highlight_text3",
                    "about_us_homepage_image1",
                    "about_us_homepage_image2",
                ),
            },
        ),
        (
            "Section Content",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    "section_display_header",
                    "section_display_text",
                    "section_highlight_text1",
                    "section_highlight_text2",
                    "section_highlight_text3",
                    "about_us_section_image1",
                    "about_us_section_image2",
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]

    # Enforce singleton behavior in admin
    def has_add_permission(self, request):
        return not AboutUs.objects.exists()

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        instance = AboutUs.objects.first()
        if instance:
            return redirect(
                f"/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{instance.id}/change/"
            )
        return super().changelist_view(request, extra_context)


@admin.register(Assets)
class AssetsAdmin(ModelAdmin):
    list_display = ("id", "created_at")
    readonly_fields = ("created_at",)
    fieldsets = [
        (
            "Covers",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    "login_cover",
                    "personal_area_cover",
                    "main_events_cover",
                    "main_classes_cover",
                    "personal_tickets_cover",
                    "personal_bookings_cover",
                    "contact_us_cover",
                    "cancel_cover",
                ),
            },
        ),
        (
            "Meta",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]

    def has_add_permission(self, request):
        return not Assets.objects.exists()

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        instance = Assets.objects.first()
        if instance:
            return redirect(
                f"/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{instance.id}/change/"
            )
        return super().changelist_view(request, extra_context)


@admin.register(Trainer)
class TrainerAdmin(ModelAdmin):
    list_display = ("name", "role", "instagram_link", "created_at")
    readonly_fields = (
        "created_at",
    )  # Add "profile_image_preview" if preview is enabled

    fieldsets = [
        (
            "Basic Info",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (("name", "role"),),
            },
        ),
        (
            "Media",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    (
                        "instagram_link",
                        "profile_image",
                    )
                    # "profile_image_preview",
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    readonly_fields = ("created_at",)
    filter_horizontal = ("trainers",)  # 👈 enhances M2M selection

    fieldsets = [
        (
            "Team Info",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("title", "header", "description"),
            },
        ),
        (
            "Trainers",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("trainers",),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]

    # ✅ Singleton enforcement
    def has_add_permission(self, request):
        return not Team.objects.exists()

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        team = Team.objects.first()
        if team:
            return redirect(
                f"/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{team.id}/change/"
            )
        return super().changelist_view(request, extra_context)


@admin.register(Service)
class ServiceAdmin(ModelAdmin):
    list_display = ("name", "created_at")
    readonly_fields = ("created_at",)

    fieldsets = [
        (
            "Service Info",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (("name",), "short_description", "long_description"),
            },
        ),
        (
            "Media",
            {"classes": ("gwiz-card", "gwiz-grid"), "fields": ("cover_image",)},
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]


@admin.register(Faq)
class FaqAdmin(ModelAdmin):
    list_display = ("question", "created_at")
    search_fields = ("question", "answer")
    list_filter = ("created_at",)
    ordering = ("question", "created_at")
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            "FAQ entry",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (("question",), "answer"),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    )


@admin.register(Contact)
class ContactAdmin(ModelAdmin):
    list_display = ("header", "email", "phone", "created_at")
    search_fields = ("header", "email", "phone", "address", "social", "access_key")
    list_filter = ("created_at",)
    ordering = ("header", "created_at")
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Content",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    (
                        "background_image",
                        "header",
                    ),
                    ("description",),
                ),
            },
        ),
        (
            "Contact Info",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    ("phone", "email"),
                    ("address", "social"),
                ),
            },
        ),
        (
            "Integration",
            {"classes": ("gwiz-card", "gwiz-grid"), "fields": ("access_key",)},
        ),
        (
            "Meta",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    )


@admin.register(Footer)
class FooterAdmin(ModelAdmin):
    list_display = ("slogan", "instagram_link", "tiktok_link", "created_at")
    search_fields = ("slogan", "instagram_link", "tiktok_link")
    list_filter = ("created_at",)
    ordering = ("created_at",)
    filter_horizontal = ("services",)
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Branding",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (("logo", "slogan"),),
            },
        ),
        (
            "Contact & Services",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (("contact"), "services"),
            },
        ),
        (
            "Social Media",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (("instagram_link", "tiktok_link"),),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    )


@admin.register(Homepage)
class HomepageAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    readonly_fields = ("created_at",)
    filter_horizontal = ("services", "faqs")  # 👈 enhances M2M selection

    fieldsets = [
        (
            "Main Settings",
            {"classes": ("gwiz-card", "gwiz-grid"), "fields": ("title",)},
        ),
        (
            "Content Blocks",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": (
                    ("banner", "about_us"),
                    ("service_title",),
                    "service_description",
                    "services",
                    ("faq_title",),
                    "faq_description",
                    "faqs",
                    "contact",
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("gwiz-card", "gwiz-grid"),
                "fields": ("created_at",),
            },
        ),
    ]

    def has_add_permission(self, request):
        return not Homepage.objects.exists()

    def changelist_view(self, request, extra_context=None):
        from django.shortcuts import redirect

        instance = Homepage.objects.first()
        if instance:
            return redirect(
                f"/admin/{self.model._meta.app_label}/{self.model._meta.model_name}/{instance.id}/change/"
            )
        return super().changelist_view(request, extra_context)

    def _image_preview(self, obj, field):
        img = getattr(obj, field, None)
        if not img:
            return "—"
        return format_html(
            '<img src="{}" style="max-width: 180px; height: auto;" />', img.url
        )

    def login_cover_preview(self, obj):
        return self._image_preview(obj, "login_cover")

    def personal_area_cover_preview(self, obj):
        return self._image_preview(obj, "personal_area_cover")

    def main_events_cover_preview(self, obj):
        return self._image_preview(obj, "main_events_cover")

    def main_classes_cover_preview(self, obj):
        return self._image_preview(obj, "main_classes_cover")

    def personal_tickets_cover_preview(self, obj):
        return self._image_preview(obj, "personal_tickets_cover")

    def personal_bookings_cover_preview(self, obj):
        return self._image_preview(obj, "personal_bookings_cover")

    def contact_us_cover_preview(self, obj):
        return self._image_preview(obj, "contact_us_cover")

    login_cover_preview.short_description = "Login cover"
    personal_area_cover_preview.short_description = "Personal area"
    main_events_cover_preview.short_description = "Main events"
    main_classes_cover_preview.short_description = "Main classes"
    personal_tickets_cover_preview.short_description = "Personal tickets"
    personal_bookings_cover_preview.short_description = "Personal bookings"
    contact_us_cover_preview.short_description = "Contact us"
