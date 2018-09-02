import sys
from django.db.models import Q
from django_cron import Schedule
from ..models import ExamCreationJob
from django.conf import settings
import os
import os.path
from ..cron_jobs import NonOverlappingCronJob


class ProcessStaleExamCreationJobsCronJob(NonOverlappingCronJob):

    RUN_EVERY_MINS = 1  # every minute
    MIN_MINUTES_FROM_LATEST_PING = 2
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'api.ProcessStaleExamCreationJobsCronJob'  # a unique code

    def _run(self):
        jobs = ExamCreationJob.objects.filter(Q(is_recording_done=False) & Q(is_processed=False))
        for job in jobs:
            try:
                if job.minutes_from_last_ping() >= ProcessStaleExamCreationJobsCronJob.MIN_MINUTES_FROM_LATEST_PING:
                    self.logger.info(
                        "ProcessStaleExamCreationJobsCronJob - deleting stale job id {job_id}...".format(job_id=job.id))
                    input_file = '{}/{}'.format(settings.VIDEOS_ROOT, job.video_file)
                    # finishing capture
                    try:
                        os.system("kill {0}".format(job.pid_capture))
                    except:
                        self.logger.error("ProcessStaleExamCreationJobsCronJob - Unexpected error {error}".format(
                            error=sys.exc_info()[0]))
                    # finishing stream
                    try:
                        os.system("kill {0}".format(job.pid_stream))
                    except:
                        self.logger.warning("ProcessStaleExamCreationJobsCronJob - Unexpected error {error}".format(
                            error=sys.exc_info()[0]))

                    if os.path.exists(input_file):
                        # delete files
                        self.logger.info(
                            "ProcessStaleExamCreationJobsCronJob - deleting file {input_file}".format(
                                input_file=input_file))
                        os.remove(input_file)

                    job.delete()
            except Exception as exc:
                self.logger.error("ProcessStaleExamCreationJobsCronJob - Unexpected error:", exc)

