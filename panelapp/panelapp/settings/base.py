##
## Copyright (c) 2016-2019 Genomics England Ltd.
##
## This file is part of PanelApp
## (see https://panelapp.genomicsengland.co.uk).
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
"""
Django settings for panelapp project.

Generated by 'django-admin startproject' using Django 1.11.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import urllib.parse

import dj_database_url
from celery.schedules import crontab
from django.contrib.messages import constants as message_constants

import panelapp

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "-0-&v=+ghegh&l51=rdmvz_5hlf1t-^e&#5d8f07iome#ljg=a"
)
SECURE_PROXY_SSL_HEADER = (
    os.getenv("SECURE_PROXY_SSL_HEADER_NAME", "HTTP_X_FORWARDED_PROTO"),
    "https",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(";")

PANEL_APP_BASE_URL = os.getenv("PANEL_APP_BASE_URL", "https://panelapp.local")
EMAIL_HOST = os.getenv("EMAIL_HOST", None)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", None)
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL", "PanelApp <panelapp@panelapp.local>"
)
PANEL_APP_EMAIL = os.getenv("PANEL_APP_EMAIL", "panelapp@panelapp.local")


# Application definition

DJANGO_APPS = [
    "django.contrib.sites",
    "dal",
    "dal_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

CUSTOM_APPS = [
    "markdownx",
    "markdown_deux",
    "bootstrap3",
    "django_object_actions",
    "mathfilters",
    "django_ajax",
    "rest_framework",
    "rest_framework.authtoken",
    "django_admin_listfilter_dropdown",
    "drf_yasg",
    "qurl_templatetag",
    "django_filters",
]

PROJECT_APPS = ["panelapp", "accounts", "panels", "webservices", "v1rewrites", "api"]

INSTALLED_APPS = DJANGO_APPS + CUSTOM_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "panelapp.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "panelapp.context_processors.use_cognito",
            ]
        },
    }
]

WSGI_APPLICATION = "panelapp.wsgi.application"

FILE_UPLOAD_DIRECTORY_PERMISSIONS = 755


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5324")
DATABASE_NAME = os.getenv("DATABASE_NAME", "panelapp")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgres://{DATABASE_USER}:{urllib.parse.quote(DATABASE_PASSWORD,safe='')}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    if DATABASE_USER and DATABASE_PASSWORD and DATABASE_HOST
    else None,
)
DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL, engine="django.db.backends.postgresql"
    )
}


# Admin
ADMIN_URL = os.getenv("DJANGO_ADMIN_URL", "admin/")


# Auth
AUTH_USER_MODEL = "accounts.User"
LOGIN_REDIRECT_URL = "home"
ACCOUNT_EMAIL_VERIFICATION_PERIOD = 24 * 60 * 60 * 3  # 3 days
LOGOUT_REDIRECT_URL = os.getenv("LOGOUT_REDIRECT_URL", "accounts:login")

# Logging

DJANGO_LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()

CELERY_WORKER_HIJACK_ROOT_LOGGER = False  # no.
LOG_FORMATTER_VALUES = [
    "asctime",
    "filename",
    "levelname",
    "lineno",
    "module",
    "message",
    "name",
    "pathname",
    "dd.trace_id",
    "dd.span_id",
    "task_id",
    "task_name",
]

LOG_FORMAT = " ".join(["%({0:s})".format(name) for name in LOG_FORMATTER_VALUES])
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json",},},
    "formatters": {
        "json": {
            "()": "panelapp.logs.TaskFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
        },
    },
    "loggers": {
        # all other apps
        "": {"handlers": ["console"], "level": DJANGO_LOG_LEVEL,},
        # app logs
        "panelapp": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
        "panels": {"handlers": ["console"], "level": APP_LOG_LEVEL, "propagate": False},
        "api": {"handlers": ["console"], "level": APP_LOG_LEVEL, "propagate": False},
        "webservices": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
        "accounts": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
        # celery tasks logging
        "celery.task": {
            "handlers": ["console"],
            "level": APP_LOG_LEVEL,
            "propagate": False,
        },
        # these create too much noise if set to DEBUG level
        "amqp": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "kombu.common": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "ddtrace": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", os.path.join(BASE_DIR, "_staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", os.path.join(BASE_DIR, "_mediafiles"))

# Random
MESSAGE_TAGS = {
    message_constants.DEBUG: "debug",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "danger",
}

SITE_ID = 1

# 3rd party apps setup

MARKDOWN_DEUX_STYLES = {
    "default": {"extras": {"wiki-tables": True}, "safe_mode": "escape"}
}

# CORS headers support
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/(WebServices|api/v1)/.*$"
CORS_ALLOW_METHODS = ("GET",)

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "pyamqp://localhost:5672/")

# Celery Beat Scheduler settings
CELERY_BEAT_SCHEDULE = {}

# specify celery beat tasks you want to run via env variables
ACTIVE_SCHEDULED_TASKS = os.getenv("ACTIVE_SCHEDULED_TASKS", "moi-check").split(";")
if "moi-check" in ACTIVE_SCHEDULED_TASKS:
    CELERY_BEAT_SCHEDULE["moi-check"] = {
        "task": "panels.tasks.moi_checks.moi_check",
        "schedule": crontab(
            hour=os.getenv("MOI_CHECK_HOUR", 6),
            minute=os.getenv("MOI_CHECK_MINUTE", 30),
            day_of_week=os.getenv("MOI_CHECK_DAY_OF_WEEK", "sun"),
        ),
        "options": {"queue": "panelapp"},
    }

PACKAGE_VERSION = panelapp.__version__

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "pa-cache-1",
        "TIMEOUT": None,
    }
}

REST_FRAMEWORK = {
    "PAGE_SIZE": 100,
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_VERSION": "v1",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "api_key": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": 'Format: "Token <strong>your token</strong>". You can find API token in your <a href="/accounts/profile/">profile page</a>',
        }
    }
}

DEFAULT_PANEL_TYPES = os.getenv("DEFAULT_PANEL_TYPES", "rare-disease-100k").split(",")

OMIM_API_KEY = os.getenv("OMIM_API_KEY", None)

SIGNED_OFF_MESSAGE = "The latest signed off version for the GMS is v{version}. The current version, shown here, may differ from the signed-off version."

# Health checks
HEALTH_CHECK_SERVICE_NAME = "panelapp"
HEALTH_CHECK_CACHE_SECONDS = 3
HEALTH_CHECK_TIMEOUT = 3
HEALTH_CHECK_TOKEN = os.getenv("HEALTH_CHECK_TOKEN", "panelapp-token")

HEALTH_CHECK_CRITICAL = os.getenv("HEALTH_CHECK_CRITICAL", "database,sqs,email").split(
    ","
)

HEALTH_CHECKS = os.getenv("HEALTH_CHECKS", "database,sqs,email").split(",")
