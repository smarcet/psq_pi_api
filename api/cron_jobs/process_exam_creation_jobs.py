import sys

from django.db.models import Q
from django_cron import CronJobBase, Schedule
from ..models import ExamCreationJob
import requests
from django.conf import settings
import logging
import os
from os import subprocess


class ProcessExamCreationJobsCronJob(CronJobBase):
    RUN_EVERY_MINS = 1  # every minute

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'api.ProcessExamCreationJobsCronJob'  # a unique code

    def do(self):
        logger = logging.getLogger(__name__)
        jobs = ExamCreationJob.objects.filter(Q(is_recording_done=True) & Q(is_processed=False))
        endpoint = settings.API_HOST + "/exams/upload"
        for job in jobs:
            try:
                input = '{}/{}'.format(settings.VIDEOS_ROOT, job.video_file)
                output = os.path.splitext(input)[0] + '.ogg'
                cmd = 'gst-launch-1.0 -e filesrc location={input} ! matroskademux ! jpegdec ! videoconvert ! ' \
                      'videoscale ! theoraenc ! oggmux ! filesink location={output}'.format(
                    input=input, output=output)
                subprocess.run(cmd)
                files = {'file': open(output, 'rb')}
                values = {
                    'filename': job.video_file,
                    'exercise': job.exercise_id,
                    'device': job.device_id,
                    'device_mac_address': job.device_mac_address,
                    'author': job.user_id,
                    'duration': job.exam_duration,
                    'taker': job.user_id,
                }
                session = requests.Session()
                session.verify = False
                response = session.post(endpoint, files=files, data=values)

                if response.status_code != 201:
                    logger.error("response from api {status_code}".format(
                        status_code=response.status_code,
                    ))

                    raise Exception("response from api {status_code}".format(
                        status_code=response.status_code,
                    ))

                job.mark_as_processed()
                job.save(force_update=True)

            except:
                print("Unexpected error:", sys.exc_info()[0])
