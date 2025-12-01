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
from .base import *  # noqa
import logging

logging.disable(logging.CRITICAL)

PANEL_APP_EMAIL = "test@localhost"
DEBUG = False
TEMPLATE_DEBUG = False
EMAIL_HOST = "localhost"
EMAIL_PORT = 25
EMAIL_HOST_USER = "vagrant"
EMAIL_HOST_PASSWORD = "1"

ALLOWED_HOSTS = ["localhost"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CELERY_TASK_ALWAYS_EAGER = True
# TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'
CELERY_TASK_PUBLISH_RETRY_POLICY = {"max_retries": 3}
BROKER_TRANSPORT_OPTIONS = {"socket_timeout": 5}
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_BROKER = "pyamqp://localhost:5672/"

PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

# AWS/S3 settings (required for s3_storages.py import)
AWS_REGION = "us-east-1"

# Static files
AWS_S3_STATICFILES_BUCKET_NAME = "test-static"
AWS_STATICFILES_LOCATION = ""
AWS_S3_STATICFILES_CUSTOM_DOMAIN = None
AWS_S3_STATICFILES_OBJECT_PARAMETERS = {}
AWS_STATICFILES_DEFAULT_ACL = "public-read"

# Media files
AWS_S3_MEDIAFILES_BUCKET_NAME = "test-media"
AWS_MEDIAFILES_LOCATION = ""
AWS_S3_MEDIAFILES_CUSTOM_DOMAIN = None
AWS_S3_MEDIAFILES_OBJECT_PARAMETERS = {}
AWS_MEDIAFILES_DEFAULT_ACL = "public-read"

# Reports
AWS_S3_REPORTS_BUCKET_NAME = "test-reports"
AWS_REPORTS_LOCATION = ""
AWS_S3_REPORTS_CUSTOM_DOMAIN = None
AWS_S3_REPORTS_OBJECT_PARAMETERS = {}
AWS_REPORTS_DEFAULT_ACL = "private"
