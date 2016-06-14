

def get_username(user):
    if user.first_name or user.last_name:
        return "%s %s" % (user.first_name, user.last_name)
    else:
        return user.username