import sys
from django.db.models import Q
from django_cron import CronJobBase, Schedule
from ..models import ExamCreationJob
import requests
from django.conf import settings
import logging
import os
import os.path
from django.utils.translation import ugettext_lazy as _


class ProcessExamCreationJobsCronJob(CronJobBase):

    RUN_EVERY_MINS = 1  # every minute

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'api.ProcessExamCreationJobsCronJob'  # a unique code

    def do(self):
        logger = logging.getLogger('cronjobs')
        jobs = ExamCreationJob.objects.filter(Q(is_recording_done=True) & Q(is_processed=False))
        endpoint = settings.API_HOST + "/exams/upload"
        for job in jobs:
            try:

                input_file = '{}/{}'.format(settings.VIDEOS_ROOT, job.video_file)

                if not os.path.exists(input_file):
                    logger.warning("ProcessExamCreationJobsCronJob - file {input_file} does not exists, skipping it...".format(input_file=input_file))
                    continue

                logger.info("ProcessExamCreationJobsCronJob - uploading file {input_file} ...".format(input_file=input_file))

                files = {
                    'file': open(input_file, 'rb'),
                }

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
                    logger.error("ProcessExamCreationJobsCronJob - response from api {status_code}".format(
                        status_code=response.status_code,
                    ))

                    raise Exception("response from api {status_code}".format(
                        status_code=response.status_code,
                    ))

                job.mark_as_processed()
                job.save(force_update=True)
                logger.info("ProcessExamCreationJobsCronJob - job {id} processed!".format(id=job.id))

                # delete files
                logger.info("ProcessExamCreationJobsCronJob - deleting file {input_file}".format(input_file=input_file))
                os.remove(input_file)
            except:
                logger.error("ProcessExamCreationJobsCronJob - Unexpected error:", sys.exc_info()[0])
