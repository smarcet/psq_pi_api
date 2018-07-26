from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from rest_framework.response import Response
import psutil


class ProcessesCheckView(GenericAPIView):
    # open registration
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer

    @staticmethod
    def get(request, pid):
        try:
            p = psutil.Process(pid)  # The pid
            return Response(p.name(), status=status.HTTP_200_OK)
        except:
            return Response("process not found", status=status.HTTP_404_NOT_FOUND)
