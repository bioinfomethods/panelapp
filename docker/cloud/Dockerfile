FROM python:3.8.17-alpine3.18

RUN mkdir -p /app/panelapp

# Application (non-root) user
RUN adduser -D -u 1000 -s /sbin/nologin  -g app app

COPY --chown=app:app ./panelapp     /app/panelapp
COPY --chown=app:app ./setup.py ./setup.cfg ./MANIFEST.in ./VERSION     /app/
COPY --chown=app:app ./deploy/gunicorn_config.py  /app/

# Python libraries get installed as root in /pythonlib (scripts are still installed in /usr/local/bin).
# Ownership of all python modules have to be writable by the user running the application, to create __pycache__.
# After installing we are removing all system dependencies not required at runtime, within the same Docker layer
WORKDIR /app
RUN apk add --no-cache postgresql-libs curl jpeg-dev zlib-dev && \
    apk add --no-cache --virtual .build-deps gcc musl-dev curl-dev postgresql-dev build-base linux-headers libffi-dev && \
    pip install --upgrade setuptools==67.8.0 && \
    pip install . && \
    apk --purge del .build-deps && \
    chown -R app:app /usr/local/lib/python3.*

ENV PYTHONPATH /pythonlib
ENV PATH="/pythonlib:${PATH}"
ENV PYTHONUNBUFFERED 0
ENV DJANGO_SETTINGS_MODULE panelapp.settings.docker-aws
ENV DJANGO_LOG_LEVEL INFO
ENV CELERY_BROKER_URL sqs://

# Gunicorn settings
ENV GUNICORN_WORKERS 8
ENV GUNICORN_TIMEOUT 300
ENV GUNICORN_BACKLOG 4096
ENV GUNICORN_BIND 0.0.0.0:8080
ENV GUNICORN_LOG_LEVEL INFO
EXPOSE 8080

WORKDIR /app/panelapp
ENTRYPOINT ["/bin/sh"]
USER app:app
