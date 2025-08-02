from django.urls import path

from .app_urls.banner_views import BannerDetailView, BannerListView

urlpatterns = [
    path("banners", BannerListView.as_view()),
    path("banner/detail/<uuid:pk>", BannerDetailView.as_view()),
]
