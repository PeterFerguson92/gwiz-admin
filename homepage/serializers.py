from homepage.models import AboutUs, Banner, Faq, Homepage, Service, Team, Trainer
from rest_framework import serializers


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"

        
class TrainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trainer
        fields = "__all__"

class TeamSerializer(serializers.ModelSerializer):
    trainers = TrainerSerializer(read_only=True, many=True)
    class Meta:
        model = Team
        fields = "__all__"

class AboutUsSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)

    class Meta:
        model = AboutUs
        fields = "__all__"

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__" 

class FaqSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faq
        fields = "__all__"    
        
class HomepageSerializer(serializers.ModelSerializer):
    banner = BannerSerializer(read_only=True)
    about_us = AboutUsSerializer(read_only=True)
    services = ServiceSerializer(read_only=True, many=True)
    faqs = FaqSerializer(read_only=True, many=True)
    class Meta:
        model = Homepage
        fields = "__all__"
