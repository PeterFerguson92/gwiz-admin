from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from homepage.models import (
    AboutUs,
    Assets,
    Banner,
    Contact,
    Faq,
    Footer,
    Homepage,
    Service,
    Team,
    Trainer,
)
from homepage.serializers import (
    AboutUsSerializer,
    AssetsSerializer,
    BannerSerializer,
    ContactSerializer,
    FaqSerializer,
    FooterSerializer,
    HomepageSerializer,
    ServiceSerializer,
    TeamSerializer,
    TrainerSerializer,
)


# BANNER VIEWS.
class BannerListView(generics.GenericAPIView):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Banner.objects.all()
        if not objects:
            return Response(
                {"status": "No banner data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class BannerDetailView(generics.GenericAPIView):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Banner.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Banner with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# ABOUT US VIEWS.
class AboutUsListView(generics.GenericAPIView):
    serializer_class = AboutUsSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = AboutUs.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class AboutUsDetailView(generics.GenericAPIView):
    serializer_class = AboutUsSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return AboutUs.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"About us with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# TRAINER VIEWS.
class TrainerListView(generics.GenericAPIView):
    serializer_class = TrainerSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Trainer.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class TrainerDetailView(generics.GenericAPIView):
    serializer_class = TrainerSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Trainer.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Trainer with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# TEAM VIEWS.
class TeamListView(generics.GenericAPIView):
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Team.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class TeamDetailView(generics.GenericAPIView):
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Team.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Team with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# SERVICE VIEWS.
class ServiceListView(generics.GenericAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Service.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class ServiceDetailView(generics.GenericAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Service.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Service with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# FAQ VIEWS.
class FaqListView(generics.GenericAPIView):
    serializer_class = FaqSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Faq.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class FaqDetailView(generics.GenericAPIView):
    serializer_class = FaqSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Faq.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Faq with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# CONTACT VIEWS.
class ContactListView(generics.GenericAPIView):
    serializer_class = ContactSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Contact.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class ContactDetailView(generics.GenericAPIView):
    serializer_class = ContactSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Contact.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Contact with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# FOOTER VIEWS.
class FooterListView(generics.GenericAPIView):
    serializer_class = FooterSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Footer.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class FooterDetailView(generics.GenericAPIView):
    serializer_class = FooterSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Footer.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Footer with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})


# ASSETS VIEWS
class AssetsListView(generics.GenericAPIView):
    serializer_class = AssetsSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Assets.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class AssetsDetailView(generics.GenericAPIView):
    serializer_class = AssetsSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Assets.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk=pk)
        if obj is None:
            return Response(
                {"status": "fail", "message": f"Assets with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(obj)
        return Response({"status": "success", "result": serializer.data})


# HOMEPAGE VIEWS.
class HomepageListView(generics.GenericAPIView):
    serializer_class = HomepageSerializer
    permission_classes = [AllowAny]

    def get(self, request):
        objects = Homepage.objects.all()
        if not objects:
            return Response(
                {"status": "No data available"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(objects, many=True)
        return Response({"status": "success", "result": serializer.data})


class HomepageDetailView(generics.GenericAPIView):
    serializer_class = HomepageSerializer
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return Homepage.objects.get(pk=pk)
        except:
            return None

    def get(self, request, pk):
        object = self.get_object(pk=pk)
        if object is None:
            return Response(
                {"status": "fail", "message": f"Homepage with Id: {pk} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(object)
        return Response({"status": "success", "result": serializer.data})
