from django.db import models
from model_utils.models import TimeStampedModel


class ExamCreationJob(TimeStampedModel):
    pid = models.PositiveIntegerField(null=False)
    user_id = models.PositiveIntegerField(null=False)
    exercise_id = models.PositiveIntegerField(null=False)
    device_id = models.PositiveIntegerField(null=False)
    video_file = models.CharField(max_length=1024, null=False)
    is_processed = models.BooleanField(default=False)
    is_recording_done = models.BooleanField(default=False)
