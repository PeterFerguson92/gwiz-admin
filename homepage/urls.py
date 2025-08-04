from django.urls import path

from homepage.app_views.banner_views import BannerDetailView, BannerListView



urlpatterns = [
    path("banners", BannerListView.as_view()),
    path("banner/detail/<uuid:pk>", BannerDetailView.as_view()),
]
