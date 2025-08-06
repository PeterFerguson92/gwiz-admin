from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response

from homepage.models import Banner, AboutUs, Homepage, Team, Trainer
from homepage.serializers import BannerSerializer, AboutUsSerializer, HomepageSerializer, TeamSerializer, TrainerSerializer


# BANNER VIEWS.
class BannerListView(generics.GenericAPIView):
    serializer_class = BannerSerializer

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
    
# HOMEPAGE VIEWS.
class HomepageListView(generics.GenericAPIView):
    serializer_class = HomepageSerializer

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
