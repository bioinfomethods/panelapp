"""
Django settings for panelapp project.

Generated by 'django-admin startproject' using Django 1.11.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import dj_database_url
from django.contrib.messages import constants as message_constants

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', '-0-&v=+ghegh&l51=rdmvz_5hlf1t-^e&#5d8f07iome#ljg=a')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [host for host in os.getenv('ALLOWED_HOSTS', '').split(';')]

EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'vagrant'
EMAIL_HOST_PASSWORD = '1'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'PanelApp <panelapp@genomicsengland.co.uk>')
PANEL_APP_EMAIL = os.getenv('PANEL_APP_EMAIL', "panelapp@genomicsengland.co.uk")


# Application definition

DJANGO_APPS = [
    'django.contrib.sites',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

CUSTOM_APPS = [
    'markdownx',
    'markdown_deux',
    'bootstrap3',
    'django_object_actions',
    'mathfilters',
    'django_ajax',
    'rest_framework',
]

PROJECT_APPS = [
    'panelapp',
    'accounts',
    'panels',
    'webservices',
    'v2import',
    'v1rewrites',
]

INSTALLED_APPS = DJANGO_APPS + CUSTOM_APPS + PROJECT_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'panelapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'panelapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(engine="django.db.backends.postgresql")
}


# Auth
AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'home'

# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.getenv(
    'STATIC_ROOT',
    os.path.join(BASE_DIR, '_staticfiles')
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv(
    'MEDIA_ROOT',
    os.path.join(BASE_DIR, '_mediafiles')
)

# Random
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger'
}

SITE_ID = 1

# 3rd party apps setup

MARKDOWN_DEUX_STYLES = {
    "default": {
        "extras": {
            "wiki-tables": True
        },
        "safe_mode": "escape",
    },
}

PANEL_APP_EMAIL = None
CELL_BASE_CONNECTOR_REST = os.getenv(
    "CELL_BASE_CONNECTOR_REST",
    "http://bioinfo.hpc.cam.ac.uk/cellbase/webservices/rest/"
)
HEALTH_CHECK_TOKEN = os.getenv('HEALTH_CHECK_TOKEN', None)
