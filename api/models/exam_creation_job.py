import pytz
from django.db import models
from model_utils.models import TimeStampedModel
from macaddress.fields import MACAddressField
from datetime import datetime


class ExamCreationJob(TimeStampedModel):

    pid_capture = models.PositiveIntegerField(null=False)
    pid_stream = models.PositiveIntegerField(null=False)
    user_id = models.PositiveIntegerField(null=False)
    exercise_id = models.PositiveIntegerField(null=False)
    device_id = models.PositiveIntegerField(null=False)
    device_mac_address = MACAddressField(integer=False, unique=False)
    video_file = models.CharField(max_length=1024, null=False)
    is_processed = models.BooleanField(default=False)
    is_recording_done = models.BooleanField(default=False)
    exam_duration = models.IntegerField(blank=True, null=True)
    last_ping = models.DateTimeField(auto_now_add=False)

    def mark_as_processed(self):
        self.is_processed = True

    def do_ping(self):
        self.last_ping = datetime.utcnow().replace(tzinfo=pytz.UTC)
        self.save()

    def minutes_from_last_ping(self):
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        last_ping = self.last_ping.replace(tzinfo=pytz.UTC)
        diff = now - last_ping
        return int(diff.total_seconds() / 60)
