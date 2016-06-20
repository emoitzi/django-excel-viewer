import json

from django.contrib import messages
from django.utils.encoding import force_text

# source: http://hunterford.me/django-messaging-for-ajax-calls-using-jquery/
class AjaxMessaging(object):
    def process_response(self, request, response):
        if request.is_ajax():
            if response['Content-Type'] in ["application/javascript", "application/json"]:
                try:
                    if type(response.content) is bytes:
                        content = json.loads(response.content.decode())
                    else:
                        content = json.loads(response.content)
                except ValueError:
                    return response

                django_messages = []

                for message in messages.get_messages(request):
                    django_messages.append({
                        "level": message.level,
                        "message": force_text(message.message),
                        "extra_tags": message.tags,
                    })

                content['django_messages'] = django_messages

                response.content = json.dumps(content)
        return response
