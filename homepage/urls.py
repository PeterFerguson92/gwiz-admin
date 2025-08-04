from django.urls import path

from homepage.app_views.banner_views import BannerDetailView, BannerListView
from homepage.app_views.homepage_view import HomepageDetailView, HomepageListView



urlpatterns = [
    path("", HomepageListView.as_view()),
    path("detail/<uuid:pk>", HomepageDetailView.as_view()),
    path("banners", BannerListView.as_view()),
    path("banner/detail/<uuid:pk>", BannerDetailView.as_view()),
]
