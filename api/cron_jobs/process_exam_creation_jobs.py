import sys

from django.db.models import Q
from django_cron import CronJobBase, Schedule
from ..models import ExamCreationJob
import requests
from django.conf import settings


class ProcessExamCreationJobsCronJob(CronJobBase):
    RUN_EVERY_MINS: int = 1  # every minute

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'api.ProcessExamCreationJobsCronJob'  # a unique code

    def do(self):
        jobs = ExamCreationJob.objects.filter(Q(is_recording_done=True) & Q(is_processed=False))
        endpoint = settings.API_HOST + "/exams/upload"
        for job in jobs:
            try:
                files = {'file': open('{}/{}'.format(settings.VIDEOS_ROOT, job.video_file), 'rb')}
                values = {
                    'filename': job.video_file,
                    'exercise': job.exercise_id,
                    'device': job.device_id,
                    'device_mac_address': job.device_mac_address,
                    'author': job.user_id,
                    'duration': job.exam_duration,
                    'taker': job.user_id,
                }
                response = requests.post(endpoint, files=files, data=values)

                if response.status_code != 201:
                    raise Exception

                job.mark_as_processed()
                job.save(force_update=True)
            except:
                print("Unexpected error:", sys.exc_info()[0])