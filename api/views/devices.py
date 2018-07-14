import os
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from django.conf import settings
import requests
from rest_framework.response import Response
from ..models import ExamCreationJob
from ..utils import get_mac_address
import socket
import subprocess
import time
import sys
from datetime import datetime, timezone
import logging

class DeviceOpenRegistrationView(GenericAPIView):
    # open registration
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer

    @staticmethod
    def post(request):
        logger = logging.getLogger(__name__)
        try:
            # current device data
            data = {
                'mac_address': get_mac_address(),
                'last_know_ip': socket.gethostbyname(socket.gethostname())
            }

            endpoint = settings.API_HOST + "/devices/current/registration"
            session = requests.Session()
            session.verify = False
            response = session.post(endpoint, data=data)

            return Response(response.json(), status=response.status_code)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            return Response(sys.exc_info()[0], status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeviceStartRecordingView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            logger = logging.getLogger(__name__)

            device_id = kwargs['device_id']
            user_id = kwargs['user_id']
            exercise_id = str(kwargs['exercise_id'])
            stream_param = '-s{}'.format(settings.STREAM_HOST)
            timestamp = int(time.time())
            file_name = "{}_{}_{}.mkv".format(user_id, exercise_id, timestamp)
            output_file = '-o{}/{}'.format(settings.VIDEOS_ROOT, file_name)
            python_interpreter = '{}/.env/bin/python'.format(settings.BASE_DIR)
            capture_script = '{}/api/utils/capture_stream.py'.format(settings.BASE_DIR)

            cmd = [python_interpreter,
                   capture_script,
                   stream_param,
                   output_file]

            logger.error('command {python_interpreter} {capture_script} {stream_param} {output_file}'.format(
                python_interpreter=python_interpreter,
                capture_script=capture_script,
                stream_param=stream_param,
                output_file=output_file
            ))

            proc = subprocess.Popen(cmd)
            time.sleep(3)
            job = ExamCreationJob()
            job.pid = proc.pid
            job.user_id = user_id
            job.exercise_id = exercise_id
            job.device_id = device_id
            job.video_file = file_name
            job.is_recording_done = False
            job.is_processed = False
            job.device_mac_address = get_mac_address()
            job.save()

            return Response({
                "pid": proc.pid,
                "id": job.id
            }, status=status.HTTP_201_CREATED)

        except:
            logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            print("Unexpected error:", sys.exc_info()[0])
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeviceStopRecordingView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer
    WAIT_TIME = 5

    @staticmethod
    def put(request, *args, **kwargs):
        try:
            job_id = kwargs['job_id']
            job = ExamCreationJob.objects.get(pk=job_id)
            if job is None:
                return Response({}, status.HTTP_404_NOT_FOUND)
            os.system("kill {0}".format(job.pid))
            job.is_recording_done = True
            now = datetime.now(timezone.utc)
            delta = now - job.created
            job.exam_duration = delta.seconds - DeviceStopRecordingView.WAIT_TIME
            job.save()

            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
