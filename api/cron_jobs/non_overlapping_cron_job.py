from django_cron import CronJobBase
import logging
import os
from django.db import transaction


class NonOverlappingCronJob(CronJobBase):
    code = 'api.NonOverlappingCronJob'  # a unique code

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('cronjobs')

    @transaction.atomic
    def _run(self):
        pass

    def do(self):
        lock_file = os.path.join("/tmp", "{filename}.lock".format(filename=self.code))

        if os.path.exists(lock_file):
            self.logger.info(
                "{class_name} - is already running, skipping it".format(class_name=self.__class__.__name__))
            return

        try:
            self.logger.info("running {class_name}".format(class_name=self.__class__.__name__))

            open(lock_file, 'w').close()
            self._run()

        except Exception as exc1:
            self.logger.error("{class_name} - error".format(class_name=self.__class__.__name__), exc1)

        finally:
            if os.path.exists(lock_file):
                self.logger.info("{class_name} - deleting file {lock_file}".format(class_name=self.__class__.__name__,
                                                                                   lock_file=lock_file))
                os.remove(lock_file)

        self.logger.info("{class_name} - finishing".format(class_name=self.__class__.__name__))
