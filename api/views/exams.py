from rest_framework import serializers, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import ExamCreationJob
from ..utils import get_mac_address
import sys
import logging
import hmac
import hashlib
import base64
import urllib.parse
import backend.settings as settings
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json


class ExamGenerateShareUrlView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.Serializer
    queryset = ExamCreationJob.objects.all()

    @staticmethod
    def get(request, *args, **kwargs):
        logger = logging.getLogger('api')
        try:
            secret = get_mac_address()
            device_id = int(request.GET.get("device_id"))
            exercise_id = int(request.GET.get("exercise_id"))
            exercise_max_duration = int(request.GET.get("exercise_max_duration"))  # in seconds
            user_id = int(request.GET.get("user_id"))
            now = datetime.utcnow()
            seconds = exercise_max_duration + (exercise_max_duration * 2)
            expires = now + relativedelta(seconds=seconds)
            logger.info("ExamGenerateShareUrlView - expiration will be on expires {expires}".format(
                expires=expires.strftime("%c")))
            expires = int(expires.timestamp())

            str_to_sign = "GET\n%s\n%s\n%s\n%s\n%s" % (device_id, exercise_id, exercise_max_duration, user_id, expires)
            h = hmac.new(bytearray(secret, 'utf-8'), str_to_sign.encode('utf-8'), hashlib.sha1)
            digest = h.digest()
            signature = urllib.parse.quote_plus(base64.b64encode(digest))
            long_url = "{host}/guest/stream?expires={expires}&signature={signature}&device_id={" \
                       "device_id}&exercise_id={exercise_id}&user_id={user_id}&exercise_max_duration={" \
                       "exercise_max_duration}".format(
                host=settings.WEB_HOST,
                expires=expires,
                signature=signature,
                device_id=device_id,
                exercise_id=exercise_id,
                exercise_max_duration=exercise_max_duration,
                user_id=user_id
            )

            post_url = 'https://firebasedynamiclinks.googleapis.com/v1/shortLinks?key={}'.format(
                settings.FIREBASE_WEB_API_KEY)
            # logger.info(post_url)
            payload = {
                "dynamicLinkInfo": {
                    "domainUriPrefix": settings.FIREBASE_DYN_LINK_DOMAIN_PREFIX,
                    "link": long_url
                },
                "suffix": {
                    "option": "UNGUESSABLE"
                }
            }

            headers = {'content-type': 'application/json'}
            r = requests.post(post_url, data=json.dumps(payload), headers=headers)
            json_response = r.json()

            if r.status_code != status.HTTP_200_OK:
                return Response(json_response, status=r.status_code)

            return Response({
                'url': json_response["shortLink"]
            }, status=status.HTTP_200_OK)

        except:
            print("Unexpected error:", sys.exc_info()[0])
            logger.error("Unexpected error {error}".format(error=sys.exc_info()[0]))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
