from django.utils.html import format_html
from django.contrib import admin
from unfold.admin import ModelAdmin
from homepage.models import AboutUs, Banner, Homepage, Service, Team, Trainer


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
                "fields": ["logo"],
            },
        ),
        (
            "Slide 1",
            {
                "fields": [
                    "img_slide_1",
                    "title_slide_1",
                    "subtitle_slide_1",
                ],
            },
        ),
        (
            "Slide 2",
            {
                "fields": [
                    "img_slide_2",
                    "title_slide_2",
                    "subtitle_slide_2",
                ],
            },
        ),
        (
            "Slide 3",
            {
                "fields": [
                    "img_slide_3",
                    "title_slide_3",
                    "subtitle_slide_3",
                ],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["created_at"],
            },
        ),
    ]

    unfold_fieldsets_in_tabs = True


@admin.register(AboutUs)
class AboutUsAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    readonly_fields = ("created_at",)

    fieldsets = [
        ("General", {"fields": ("title", "cover_image", "team")}),
        (
            "Homepage Display",
            {
                "fields": (
                    "homepage_display_header",
                    "homepage_display_text",
                    "highlight_text1",
                    "highlight_text2",
                    "highlight_text3",
                    "about_us_homepage_image1",
                    "about_us_homepage_image2",
                )
            },
        ),
        (
            "Section Content",
            {
                "fields": (
                    "section_display_header",
                    "section_display_text",
                    "section_highlight_text1",
                    "section_highlight_text2",
                    "section_highlight_text3",
                    "about_us_section_image1",
                    "about_us_section_image2",
                )
            },
        ),
        ("Metadata", {"fields": ("created_at",)}),
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
                "fields": (
                    "name",
                    "role",
                    "instagram_link",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "profile_image",
                    # "profile_image_preview",  # optional — see below
                )
            },
        ),
        ("Metadata", {"fields": ("created_at",)}),
    ]


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    readonly_fields = ("created_at",)
    filter_horizontal = ("trainers",)  # 👈 enhances M2M selection

    fieldsets = [
        ("Team Info", {"fields": ("title", "header", "description")}),
        ("Trainers", {"fields": ("trainers",)}),
        ("Metadata", {"fields": ("created_at",)}),
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
        ("Service Info", {"fields": ("name", "short_description", "long_description")}),
        ("Media", {"fields": ("cover_image",)}),
        ("Metadata", {"fields": ("created_at",)}),
    ]

@admin.register(Homepage)
class HomepageAdmin(ModelAdmin):
    list_display = ("title", "created_at")
    readonly_fields = ("created_at",)
    filter_horizontal = ("services",)  # 👈 enhances M2M selection

    fieldsets = [
        ("Main Settings", {
            "fields": ("title",)
        }),
        ("Content Blocks", {
            "fields": (
                "banner",
                "about_us",
                "services",
            )
        }),
        ("Metadata", {
            "fields": ("created_at",)
        }),
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

