from django.utils.html import format_html
from django.contrib import admin
from unfold.admin import ModelAdmin
from homepage.models import Banner, Homepage


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


@admin.register(Homepage)
class HomepageAdmin(ModelAdmin):
    search_fields = ("title__startswith",)
    filter_horizontal = ("banner",)
    fields = (
        "title",
        "banner",
    )
    list_display = (
        "title",
        "created_at",
    )
    list_filter = (
        "title",
        "created_at",
    )
