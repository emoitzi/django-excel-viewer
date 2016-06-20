from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView


class SettingsView(TemplateView):

    def has_facebook(self):
        accounts = self.request.user.socialaccount_set.filter(provider='facebook')
        return accounts.exists()

    def has_google(self):
        accounts = self.request.user.socialaccount_set.filter(provider='google')
        return accounts.exists()

    def get_context_data(self, **kwargs):
        context = super(SettingsView, self).get_context_data(**kwargs)
        context.update({
            "has_facebook": self.has_facebook(),
            "has_google": self.has_google(),
        })
        return context


user_settings = login_required(SettingsView.as_view(template_name='users/settings.html'))