from rest_framework.generics import ListAPIView
from django.db.models import Q

from ..serializers.exam_creation_jobs_serializers import ReadOnlyExamCreationJobsSerializer
from ..models import ExamCreationJob


class ExamCreationJobsListAPIView(ListAPIView):
    queryset = ExamCreationJob.objects.filter(Q(is_processed=False)).all().order_by('id')
    serializer_class = ReadOnlyExamCreationJobsSerializer
