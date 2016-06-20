from celery import shared_task


@shared_task
def send_editor_mail(request_id):
    from frontend.models import ChangeRequest
    change_request = ChangeRequest.objects.get(pk=request_id)
    change_request.send_editor_mail()


@shared_task
def send_new_status_notification_mail(request_id):
    from frontend.models import ChangeRequest
    change_request = ChangeRequest.objects.get(pk=request_id)
    change_request.send_new_status_notification_mail()
