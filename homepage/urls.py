from django.urls import path

from homepage.views import AboutUsDetailView, AboutUsListView, BannerDetailView, BannerListView, HomepageDetailView, HomepageListView




urlpatterns = [
    path("", HomepageListView.as_view()),
    path("detail/<uuid:pk>", HomepageDetailView.as_view()),
    
    path("banners", BannerListView.as_view()),
    path("banner/detail/<uuid:pk>", BannerDetailView.as_view()),
    
    path("about-us", AboutUsListView.as_view()),
    path("about-us/detail/<uuid:pk>", AboutUsDetailView.as_view()),
]
