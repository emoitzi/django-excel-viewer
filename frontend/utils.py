

def show_debug_toolbar(request):
    if request.is_ajax():
        return False
    if request.user.is_superuser:
        return True
    if request.get_host() == "127.0.0.1:8000" or \
            request.get_host() == "localhost:8000":
        return True
    return False
