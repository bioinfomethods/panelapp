ARG python_base=python:3.11.9-alpine3.19
ARG node_base=node:20.14.0-alpine3.19


FROM ${node_base} as frontend_build

COPY ./frontend /src/frontend
COPY ./webpack.* package.json package-lock.json /src/

RUN cd /src && npm ci && npm run build

FROM ${python_base} as backend_build_prod

ENV POETRY_VERSION=1.8.3

WORKDIR /src

RUN apk upgrade --no-cache && \
    apk add --no-cache postgresql-libs curl jpeg-dev zlib-dev && \
    apk add --no-cache musl-dev curl-dev postgresql-dev build-base linux-headers libffi-dev && \
    python3 -m venv /src/.poetry && \
    /src/.poetry/bin/pip install -U pip setuptools && \
    /src/.poetry/bin/pip install poetry=="$POETRY_VERSION" && \
    /src/.poetry/bin/poetry self add poetry-plugin-bundle

COPY ./pyproject.toml ./poetry.lock ./README.md /src/
COPY ./panelapp /src/panelapp

RUN /src/.poetry/bin/poetry bundle venv --only main,deploy /venv && \
    # Resolve https://nvd.nist.gov/vuln/detail/CVE-2024-23342
    # https://github.com/python-poetry/poetry/issues/5330#issuecomment-1907083739
    /venv/bin/pip uninstall -y ecdsa

FROM ${python_base} as base

WORKDIR /app

# Application (non-root) user
RUN adduser -D -u 1000 -s /sbin/nologin  -g app app && \
    chown app:app /app

RUN apk upgrade --no-cache && \
    apk add --no-cache postgresql-libs curl jpeg-dev zlib-dev

COPY --chown=app:app ./deploy/gunicorn_config.py /app/
COPY --chown=app:app --from=frontend_build /src/webpack-stats.json /app/
COPY --chown=app:app --from=frontend_build /src/dist /app/dist

ENV CELERY_BROKER_URL=sqs://

# Gunicorn settings
ENV GUNICORN_WORKERS=8
ENV GUNICORN_TIMEOUT=300
ENV GUNICORN_BACKLOG=4096
ENV GUNICORN_BIND=0.0.0.0:8080
ENV GUNICORN_LOG_LEVEL=INFO
EXPOSE 8080

# virtualenv
ENV VIRTUAL_ENV=/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV STATICFILES_DIRS=/app/dist
ENV WEBPACK_LOADER_STATS_FILE=/app/webpack-stats.json

USER app:app

FROM backend_build_prod as backend_build_dev

RUN /src/.poetry/bin/poetry bundle venv --with deploy /venv

FROM base as dev

COPY --chown=app:app --from=backend_build_dev /venv /venv

FROM base as test

COPY --chown=app:app --from=backend_build_dev /venv /venv
COPY --chown=app:app ./frontend/tests/data.json /app/data.json

FROM base as prod

COPY --chown=app:app --from=backend_build_prod /venv /venv
