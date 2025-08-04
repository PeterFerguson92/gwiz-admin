from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response

from homepage.models import Homepage
from homepage.serializers import BannerSerializer, HomepageSerializer


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
