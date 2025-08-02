# Register your models here.
from django.contrib import admin
from homepage.models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    search_fields = ("title_slide_1__startswith",)
    fields = (
        "logo",
        "img_slide_1",
        "title_slide_1",
        "subtitle_slide_1",
        "img_slide_2",
        "title_slide_2",
        "subtitle_slide_2",
        "img_slide_3",
        "title_slide_3",
        "subtitle_slide_3",
    )
    list_display = (
        "title_slide_1",
        "title_slide_2",
        "title_slide_3",
        "created_at",
    )
