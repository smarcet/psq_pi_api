from rest_framework_jwt.views import (obtain_jwt_token, refresh_jwt_token)
from django.urls import path

from .views import DeviceOpenRegistrationView, DeviceStartRecordingView, DeviceStopRecordingView

urlpatterns = [
    path('devices/current/registration', DeviceOpenRegistrationView.as_view(), name='device-open-registration'),
    path('devices/<int:device_id>/users/<int:user_id>/exercises/<int:exercise_id>/record-jobs',
         DeviceStartRecordingView.as_view(),
         name='start-exercise-recording'),
    path('devices/<int:device_id>/users/<int:user_id>/exercises/<int:exercise_id>/record-jobs/<int:job_id>',
         DeviceStopRecordingView.as_view(),
         name='stop-exercise-recording'),
]
