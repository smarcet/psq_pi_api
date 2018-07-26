import sys

from django.db.models import Q
from django_cron import CronJobBase, Schedule
from ..models import ExamCreationJob
import requests
from django.conf import settings
import logging
import os
import subprocess
import os.path


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

                input_file = '{}/{}'.format(settings.VIDEOS_ROOT, job.video_file)

                if not os.path.exists(input_file):
                    print("file {input_file} does not exists, skipping it...".format(input_file=input_file))
                    continue

                output_file_ogg = os.path.splitext(input_file)[0] + '.ogg'
                output_file_webm = os.path.splitext(input_file)[0] + '.webm'
                output_file_mp4 = os.path.splitext(input_file)[0] + '.mp4'

                # ogg
                cmd = 'gst-launch-1.0 -e filesrc location={input_file} ! matroskademux ! jpegdec ! videoconvert ! ' \
                      'theoraenc bitrate=1000000 ! oggmux ! filesink location={output_file}'.format(
                    input_file=input_file, output_file=output_file_ogg)
                print("about to run command {cmd}".format(cmd=cmd))
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                process.wait()
                print("command return code {return_code}".format(return_code=process.returncode))

                # webm
                cmd = 'gst-launch-1.0 -e filesrc location={input_file} ! matroskademux ! jpegdec ! videoconvert ! ' \
                      'vp8enc ! webmmux ! filesink location={output_file}'.format(
                    input_file=input_file, output_file=output_file_webm)

                print("about to run command {cmd}".format(cmd=cmd))
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                process.wait()

                print("command return code {return_code}".format(return_code=process.returncode))

                # mp4
                cmd = 'gst-launch-1.0 -e filesrc location={input_file} ! matroskademux ! jpegdec ! videoconvert ! ' \
                      'x264enc ! qtmux ! filesink location={output_file}'.format(
                    input_file=input_file, output_file=output_file_mp4)

                print("about to run command {cmd}".format(cmd=cmd))
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                process.wait()

                print("command return code {return_code}".format(return_code=process.returncode))

                files = {
                    'file_ogg': open(output_file_ogg, 'rb'),
                    'file_webm': open(output_file_webm, 'rb'),
                    'file_mp4': open(output_file_mp4, 'rb'),
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
                    logger.error("response from api {status_code}".format(
                        status_code=response.status_code,
                    ))

                    raise Exception("response from api {status_code}".format(
                        status_code=response.status_code,
                    ))

                job.mark_as_processed()
                job.save(force_update=True)
                print("job {id} processed!".format(id=job.id))

                # delete files
                os.remove(input_file)
                #os.remove(output_file_mp4)
                #os.remove(output_file_ogg)
                #os.remove(output_file_webm)
            except:
                print("Unexpected error:", sys.exc_info()[0])
