from homepage.models import Banner, Homepage
from rest_framework import serializers


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"

class HomepageSerializer(serializers.ModelSerializer):
    banner = BannerSerializer(many=True, read_only=True)
    class Meta:
        model = Homepage
        fields = "__all__"