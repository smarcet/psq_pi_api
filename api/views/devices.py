import os
from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from django.conf import settings
import requests
from rest_framework.response import Response
from api.utils import get_video_len
from ..models import ExamCreationJob
from ..utils import get_mac_address
import socket
import subprocess
import time
import sys
import logging


class DeviceOpenRegistrationView(GenericAPIView):
    # open registration
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer
    queryset = ExamCreationJob.objects.all()

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
            logger.info("response from api http code {code}".format(code=response.status_code))
            return Response(response.json(), status=response.status_code)
        except:
            print("Unexpected error:", sys.exc_info()[0])
            logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            return Response(sys.exc_info()[0], status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeviceStartRecordingView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer
    queryset = ExamCreationJob.objects.all()
    SLEEP_INTERVAL = 3

    @staticmethod
    def post(request, *args, **kwargs):
        logger = logging.getLogger(__name__)

        try:

            device_id = kwargs['device_id']
            user_id = kwargs['user_id']
            exercise_id = str(kwargs['exercise_id'])
            stream_key = str(request.GET.get("stream_key"))

            stream_param = '-s {}'.format(settings.STREAM_HOST)
            timestamp = int(time.time())
            file_name = "{}_{}_{}.mkv".format(user_id, exercise_id, timestamp)
            output_file = '-o {}/{}'.format(settings.VIDEOS_ROOT, file_name)
            rtmp_url = '-o {}'.format(settings.RTMP_HOST)
            user_id_param = '-u {}'.format(user_id)
            exercise_id_param = '-e {}'.format(exercise_id)
            stream_key_param = '-k {}'.format(stream_key)
            type_param = '-t {}'.format(settings.DEVICE_TYPE)

            python_interpreter = '{}/.env/bin/python'.format(settings.BASE_DIR)
            capture_script = '{}/api/utils/capture_gs.py'.format(settings.BASE_DIR)
            streamer_script = '{}/api/utils/streamer_gs.py'.format(settings.BASE_DIR)

            cmd1 = [python_interpreter,
                   capture_script,
                   stream_param,
                   output_file]

            cmd2 = [python_interpreter,
                    streamer_script,
                    stream_param,
                    rtmp_url,
                    user_id_param,
                    exercise_id_param,
                    stream_key_param,
                    type_param]

            logger.info('command {python_interpreter} {capture_script} {stream_param} {output_file}'.format(
                python_interpreter=python_interpreter,
                capture_script=capture_script,
                stream_param=stream_param,
                output_file=output_file
            ))

            proc1 = subprocess.Popen(cmd1)
            proc2 = subprocess.Popen(cmd2)

            time.sleep(DeviceStartRecordingView.SLEEP_INTERVAL)
            job = ExamCreationJob()
            job.pid_capture = proc1.pid
            job.pid_stream = proc2.pid
            job.user_id = user_id
            job.exercise_id = exercise_id
            job.device_id = device_id
            job.video_file = file_name
            job.is_recording_done = False
            job.is_processed = False
            job.device_mac_address = get_mac_address()
            job.save()

            return Response({
                "pid_capture": proc1.pid,
                "pid_stream": proc2.pid,
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
    queryset = ExamCreationJob.objects.all()

    @staticmethod
    def put(request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        try:

            job_id = kwargs['job_id']
            job = ExamCreationJob.objects.get(pk=job_id)
            if job is None:
                return Response({}, status.HTTP_404_NOT_FOUND)
            # finishing capture
            try:
                os.system("kill {0}".format(job.pid_capture))
            except:
                logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            # finishing stream
            try:
                os.system("kill {0}".format(job.pid_stream))
            except:
                logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            job.is_recording_done = True
            file_name = '{}/{}'.format(settings.VIDEOS_ROOT,  job.video_file)
            total_video_duration = get_video_len(file_name)
            seconds = 0
            if total_video_duration['hours'] > 0:
                seconds += total_video_duration['hours'] /3600
            if total_video_duration['minutes'] > 0:
                seconds += total_video_duration['minutes'] / 60
            if total_video_duration['seconds'] > 0:
                seconds += int(total_video_duration['seconds'])

            job.exam_duration = seconds
            job.save()
            return Response({}, status=status.HTTP_204_NO_CONTENT)

        except:
            print("Unexpected error:", sys.exc_info()[0])
            logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
