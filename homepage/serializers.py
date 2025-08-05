from homepage.models import AboutUs, Banner, Homepage
from rest_framework import serializers


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"


class AboutUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutUs
        fields = "__all__"


class HomepageSerializer(serializers.ModelSerializer):
    banner = BannerSerializer(read_only=True)
    about_us = AboutUsSerializer(read_only=True)

    class Meta:
        model = Homepage
        fields = "__all__"
