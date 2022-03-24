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

# Gunicorn configuration file
# Iterates through all env variables named GUNICORN_* and set local variables with the suffix, lowercased: e.g.
# GUNICORN_FOO_BAR = 42 creates a local variable named foo_bar with value '42'
# Inspired by: https://sebest.github.io/post/protips-using-gunicorn-inside-a-docker-image/

import os

for k, v in os.environ.items():
    if k.startswith("GUNICORN_"):
        key = k.split("_", 1)[1].lower()
        locals()[key] = v


# Logging
DJANGO_LOG_LEVEL = os.getenv("DJANGO_LOG_LEVEL", "INFO").upper()
APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()

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

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "formatters": {
        "json": {
            "()": "panelapp.logs.TaskFormatter",
            "fmt": LOG_FORMAT,
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
        },
        "root": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
        # app loggers
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
        # other
        "gunicorn.error": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "handlers": ["console"],
            "propagate": 1,
            "qualname": "gunicorn.error",
        },
        "gunicorn.access": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "handlers": ["console"],
            "propagate": 1,
            "qualname": "gunicorn.access",
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
