from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import os
from django.conf import settings


class ProcessesCheckView(GenericAPIView):
    # open registration
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer

    @staticmethod
    def get(request, pid):
        try:
            input_file = '{base_dir}/api/run/{pid}.pid'.format(base_dir=settings.BASE_DIR,pid=pid)
            if os.path.exists(input_file):
                return Response("process found", status=status.HTTP_200_OK)
            return Response("process not found", status=status.HTTP_404_NOT_FOUND)
        except:
            return Response("process not found", status=status.HTTP_404_NOT_FOUND)
