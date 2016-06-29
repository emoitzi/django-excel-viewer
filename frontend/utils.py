

def show_debug_toolbar(request):
    if request.is_ajax():
        return False
    if request.user.is_superuser:
        return True
    if request.get_host() == "127.0.0.1:8000" or \
            request.get_host() == "localhost:8000":
        return True
    return False

def get_user_email(user):
    email = user.email
    email_address = user.emailaddress_set.get_primary(user)
    if email_address:
        email = email_address.email
    return email