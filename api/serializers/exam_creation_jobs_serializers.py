from rest_framework import serializers
from ..models import ExamCreationJob


class ReadOnlyExamCreationJobsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamCreationJob
        fields = ('taker', 'exercise', 'device', 'duration')
