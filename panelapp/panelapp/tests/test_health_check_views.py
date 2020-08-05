import json

import pytest
from django.conf import settings
from django.test import (
    RequestFactory,
    override_settings,
)
from rest_framework import status
from rest_framework.reverse import reverse

from panelapp.health.resources.database import PostgreSQL
from panelapp.health.views.health_check_views import (
    HealthCheck,
    ping,
)

HEALTH_CHECK_TOKEN = "token"


@pytest.mark.django_db
@override_settings(HEALTH_CHECK_TOKEN=HEALTH_CHECK_TOKEN)
def test_health_check_with_token():
    request = RequestFactory().get(
        path=reverse(viewname="health-check") + "?token=" + HEALTH_CHECK_TOKEN
    )
    response = HealthCheck(request=request).get(request)

    data = json.loads(response.content)

    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ]
    assert len(data["components"]) == len(settings.HEALTH_CHECKS)
    assert data["requestUrl"] == request.build_absolute_uri()
    # Currently sqs will be unavailable during testing
    assert len(data["unavailableComponents"]) == 1
    assert "datastores" in data["dependencies"]
    assert "apis" in data["dependencies"]


@pytest.mark.django_db
def test_health_check_no_token():
    request = RequestFactory().get(path=reverse(viewname="health-check"))
    response = HealthCheck(request=request).get(request)

    data = json.loads(response.content)

    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ]
    assert len(data["components"]) == len(settings.HEALTH_CHECKS)
    assert data["requestUrl"] == request.build_absolute_uri()
    assert "dependencies" not in data


@pytest.mark.django_db
@override_settings(HEALTH_CHECK_TOKEN=HEALTH_CHECK_TOKEN)
def test_health_check_with_skip():
    postgres_resource = PostgreSQL()

    request = RequestFactory().get(
        path=reverse(viewname="health-check")
        + "?token={token}&skip={skip}".format(
            token=HEALTH_CHECK_TOKEN, skip=",".join([postgres_resource.name])
        )
    )
    response = HealthCheck(request=request).get(request)
    data = json.loads(response.content)

    service_descriptions = [
        dependency["description"] for dependency in data["dependencies"]["datastores"]
    ]

    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_503_SERVICE_UNAVAILABLE,
    ]

    assert postgres_resource.name not in service_descriptions
    assert len(data["components"]) == len(settings.HEALTH_CHECKS)
    assert data["requestUrl"] == request.build_absolute_uri()


def test_ping():
    response = ping(None)
    assert response.status_code == 200
