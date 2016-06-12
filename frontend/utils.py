import django.contrib.auth.models

def show_debug_toolbar(request):
    if request.user.is_superuser and not request.is_ajax():
        return True
    if request.get_host() == "127.0.0.1:8000" or \
            request.get_host() == "localhost:8000":
        return True
    return False
