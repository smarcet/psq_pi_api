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


class ProcessStaleExamCreationJobsCronJob(CronJobBase):

    RUN_EVERY_MINS = 1  # every minute

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'api.ProcessStaleExamCreationJobsCronJob'  # a unique code

    def do(self):
        logger = logging.getLogger('cronjobs')
        jobs = ExamCreationJob.objects.filter(Q(is_recording_done=False) & Q(is_processed=False))
        for job in jobs:
            try:
                if job.minutes_from_last_ping() >= 5:
                    logger.info("ProcessStaleExamCreationJobsCronJob - deleting stale job ...")
                    input_file = '{}/{}'.format(settings.VIDEOS_ROOT, job.video_file)

                    if os.path.exists(input_file):
                        # delete files
                        logger.info(
                            "ProcessStaleExamCreationJobsCronJob - deleting file {input_file}".format(input_file=input_file))
                        os.remove(input_file)

                    job.delete()
            except:
                logger.error("ProcessStaleExamCreationJobsCronJob - Unexpected error:", sys.exc_info()[0])
