from django.urls import path

from homepage.views import (
    AboutUsDetailView,
    AboutUsListView,
    BannerDetailView,
    BannerListView,
    ContactDetailView,
    ContactListView,
    FooterDetailView,
    FooterListView,
    HomepageDetailView,
    HomepageListView,
    ServiceDetailView,
    ServiceListView,
    TeamDetailView,
    TeamListView,
    TrainerDetailView,
    TrainerListView,
)

urlpatterns = [
    path("", HomepageListView.as_view()),
    path("detail/<uuid:pk>", HomepageDetailView.as_view()),
    path("banners", BannerListView.as_view()),
    path("banner/detail/<uuid:pk>", BannerDetailView.as_view()),
    path("about-us", AboutUsListView.as_view()),
    path("about-us/detail/<uuid:pk>", AboutUsDetailView.as_view()),
    path("trainer", TrainerListView.as_view()),
    path("trainer/detail/<uuid:pk>", TrainerDetailView.as_view()),
    path("team", TeamListView.as_view()),
    path("team/detail/<uuid:pk>", TeamDetailView.as_view()),
    path("service", ServiceListView.as_view()),
    path("service/detail/<uuid:pk>", ServiceDetailView.as_view()),
    path("contact", ContactListView.as_view()),
    path("contact/detail/<uuid:pk>", ContactDetailView.as_view()),
    path("footer", FooterListView.as_view()),
    path("footer/detail/<uuid:pk>", FooterDetailView.as_view()),
]
