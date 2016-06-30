import pytz

from django.utils import timezone, translation
import logging

logger = logging.getLogger(__name__)


class TimezoneMiddleware(object):
    def process_request(self, request):
        translation.get_language()
        if translation.get_language() == 'de':
            timezone.activate(pytz.timezone('Europe/Vienna'))