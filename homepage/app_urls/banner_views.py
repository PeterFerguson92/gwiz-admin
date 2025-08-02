from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response

from homepage.models import Banner
from homepage.serializers import BannerSerializer


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
