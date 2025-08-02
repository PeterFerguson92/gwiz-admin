from django.urls import path

from .views import BannerDetailView, BannerListView

urlpatterns = [
    path("banners", BannerListView.as_view()),
    path("banner/detail/<uuid:pk>", BannerDetailView.as_view()),
]
