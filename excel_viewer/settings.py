"""
Django settings for rk_roster project.

Generated by 'django-admin startproject' using Django 1.9.6.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
from urllib.parse import urlparse


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = BASE_DIR
DATA_DIR = os.environ.get('OPENSHIFT_DATA_DIR', os.path.join(REPO_DIR, 'data'))
WSGI_DIR = os.path.join(REPO_DIR, 'wsgi')


import sys
sys.path.append(os.path.join(REPO_DIR, 'libs'))
import secrets
SECRETS = secrets.getter(os.path.join(DATA_DIR, 'secrets.json'))

SECRET_KEY = SECRETS['secret_key']

DEBUG = os.environ.get('EXCEL_VIEWER_DEBUG', 'TRUE') == 'TRUE'

from socket import gethostname
ALLOWED_HOSTS = [
    gethostname(), # For internal OpenShift load balancer security purposes.
    os.environ.get('OPENSHIFT_APP_DNS'), # Dynamically map to the OpenShift gear name.
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'debug_toolbar',
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',

    'frontend',
    'excel_import',
    'users',
]

SITE_ID = 1
MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'excel_viewer.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

WSGI_APPLICATION = 'excel_viewer.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases


DATABASES = {}
if 'OPENSHIFT_POSTGRESQL_DB_URL' in os.environ:
    url = urlparse(os.environ.get('OPENSHIFT_POSTGRESQL_DB_URL'))

    DATABASES['default'] = {
        'ENGINE' : 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['OPENSHIFT_APP_NAME'],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,
        }
else:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(DATA_DIR, 'db.sqlite3'),
        }


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG'
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            # 'stream': sys.stdout,
            'level': 'DEBUG',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.environ.get("OPENSHIFT_LOG_DIR", ""), "debug.log"),
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s  %(name)s.%(funcName)s '
                      '(%(lineno)d):'
                      '%(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(name)s: %(message)s'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'requests': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'DEBUG',
        }
    }
}

ADMINS = tuple(admin for admin in os.environ.get("EXCEL_VIEWER_ADMINS", "").split(';') if admin)

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = ( os.path.join(BASE_DIR, 'static'), )
STATIC_ROOT = os.path.join(WSGI_DIR, 'static')

MEDIA_ROOT = os.path.join(DATA_DIR, 'media')

LOGIN_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_EMAIL_VERIFICATION = False
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_DEFAULT_HTTP_PROTOCOL="http" if DEBUG else "https"

ACCOUNT_SIGNUP_FORM_CLASS = 'users.forms.SignupForm'
ACCOUNT_ADAPTER = "users.adapter.AccountAdapter"
SOCIALACCOUNT_ADAPTER = "users.adapter.SocialAccountAdapter"



SOCIALACCOUNT_PROVIDERS = \
    {'facebook':
       {'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile', ],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': True,
        'VERSION': 'v2.4'}}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if 'EXCEL_VIEWER_MAIL_URL' in os.environ:
    url = urlparse(os.environ.get('EXCEL_VIEWER_MAIL_URL'))
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = url.hostname
    EMAIL_PORT = url.port
    EMAIL_HOST_USER = url.username
    EMAIL_HOST_PASSWORD  = url.password
    EMAIL_USE_TLS = True

if 'EXCEL_VIEWER_DEFAULT_FROM_EMAIL' in os.environ:
    DEFAULT_FROM_EMAIL = os.environ.get('EXCEL_VIEWER_DEFAULT_FROM_EMAIL')

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions'
    ]
}

DEBUG_TOOLBAR_PATCH_SETTINGS = True
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': 'frontend.utils.show_debug_toolbar',
}
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel'
]
