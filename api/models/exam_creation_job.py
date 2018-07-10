from django.db import models
from model_utils.models import TimeStampedModel
from macaddress.fields import MACAddressField


class ExamCreationJob(TimeStampedModel):
    pid = models.PositiveIntegerField(null=False)
    user_id = models.PositiveIntegerField(null=False)
    exercise_id = models.PositiveIntegerField(null=False)
    device_id = models.PositiveIntegerField(null=False)
    device_mac_address = MACAddressField(integer=False, unique=False)
    video_file = models.CharField(max_length=1024, null=False)
    is_processed = models.BooleanField(default=False)
    is_recording_done = models.BooleanField(default=False)
    exam_duration = models.IntegerField(blank=True, null=True)

    def mark_as_processed(self):
        self.is_processed = True
