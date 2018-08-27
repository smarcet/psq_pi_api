import hashlib
from django.db.models import Q

from ..cron_jobs import NonOverlappingCronJob
from ..models import ExamCreationJob
import requests
from django.conf import settings
import os
import os.path


class ProcessExamCreationJobsCronJob(NonOverlappingCronJob):

    RUN_EVERY_MINS = 1  # every minute
    CHUNK_SIZE = 1024 * 1024 * 1
    code = 'api.ProcessExamCreationJobsCronJob'  # a unique code

    def md5(self, input_file):
        hash_md5 = hashlib.md5()
        with open(input_file, "rb") as f:
            for chunk in iter(lambda: f.read(ProcessExamCreationJobsCronJob.CHUNK_SIZE), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _run(self):
        jobs = ExamCreationJob.objects.filter(Q(is_recording_done=True) & Q(is_processed=False))
        for job in jobs:
            try:

                endpoint = settings.API_HOST + "/exams/upload"
                input_file = '{}/{}'.format(settings.VIDEOS_ROOT, job.video_file)

                if not os.path.exists(input_file):
                    self.logger.warning(
                        "ProcessExamCreationJobsCronJob - file {input_file} does not exists, skipping it...".format(
                            input_file=input_file))
                    job.delete()
                    continue

                self.logger.info(
                    "ProcessExamCreationJobsCronJob - generating md5 checksum of file {input_file} ...".format(
                        input_file=input_file))

                file_md5_checksum = self.md5(input_file)

                self.logger.info(
                    "ProcessExamCreationJobsCronJob - uploading file {input_file} ...".format(input_file=input_file))
                with open(input_file, 'rb') as raw_video_file:

                    session = requests.Session()
                    session.verify = False
                    bytes_size = os.path.getsize(input_file)
                    bytes_read = 0
                    chunk_nbr = 1

                    while True:
                        chunk = raw_video_file.read(ProcessExamCreationJobsCronJob.CHUNK_SIZE)
                        if not chunk:
                            break

                        files = {
                            'file': chunk,
                        }

                        values = {
                            'filename': job.video_file
                        }
                        headers = {
                            'Content-Range': "bytes {range_start}-{range_end}/{file_size}".format(
                                range_start=bytes_read,
                                range_end=bytes_read + (len(chunk) - 1),
                                file_size=bytes_size
                            )
                        }

                        bytes_read += len(chunk)

                        self.logger.info(
                            "ProcessExamCreationJobsCronJob - uploading file {input_file} chunk {chunk_nbr} "
                            "bytes_read {bytes_read}...".format(
                                input_file=input_file,
                                bytes_read=bytes_read,
                                chunk_nbr=chunk_nbr
                            ))

                        response = session.put(endpoint, files=files, headers=headers, data=values)

                        if response.status_code != 200:
                            logger.error("ProcessExamCreationJobsCronJob - response from api {status_code}".format(
                                status_code=response.status_code,
                            ))

                            raise Exception("response from api {status_code}".format(
                                status_code=response.status_code,
                            ))
                        json = response.json()
                        endpoint = json['url']
                        chunk_nbr = chunk_nbr + 1

                    values = {
                        'filename': job.video_file,
                        'exercise': job.exercise_id,
                        'device': job.device_id,
                        'device_mac_address': job.device_mac_address,
                        'author': job.user_id,
                        'duration': job.exam_duration,
                        'taker': job.user_id,
                        "md5": file_md5_checksum
                    }

                    self.logger.info(
                        "ProcessExamCreationJobsCronJob - doing final post for file {input_file} chunk {chunk_nbr} bytes_read {bytes_read}...".format(
                            input_file=input_file,
                            bytes_read=bytes_read,
                            chunk_nbr=chunk_nbr
                        ))

                    response = session.post(endpoint, data=values)

                    if response.status_code != 200:
                        self.logger.error("ProcessExamCreationJobsCronJob - response from api {status_code}".format(
                            status_code=response.status_code,
                        ))

                        raise Exception("response from api {status_code}".format(
                            status_code=response.status_code,
                        ))

                    json = response.json()

                    job.mark_as_processed()
                    job.save(force_update=True)
                    self.logger.info("ProcessExamCreationJobsCronJob - job {id} processed!".format(id=job.id))

                    # delete files
                    self.logger.info(
                        "ProcessExamCreationJobsCronJob - deleting file {input_file}".format(input_file=input_file))
                    os.remove(input_file)

            except Exception as exc:
                self.logger.error("ProcessExamCreationJobsCronJob - Unexpected error:", exc)

