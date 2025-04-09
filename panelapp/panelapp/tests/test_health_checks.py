import json

import pytest
from django.conf import settings
from django.test import (
    RequestFactory,
    override_settings,
)
from rest_framework.reverse import reverse

from panelapp.health.enums import Status
from panelapp.health.health_checks import HealthChecks
from panelapp.health.resources.database import PostgreSQL
from panelapp.health.resources.email import Email
from panelapp.health.resources.sqs import SQS

OK_PAYLOAD = json.dumps({"response": [{"result": [{"ok": True}]}]})


@pytest.mark.django_db
def test_default_settings():
    """Test if we have missing health check specified in the settings.

    By default all health checks should be in `HEALTH_CHECKS`.
    """

    checks = HealthChecks()

    for name in settings.HEALTH_CHECKS:
        assert HealthChecks.get_module(name) is not None

    assert len(checks.resources) == len(settings.HEALTH_CHECKS)


@pytest.mark.django_db
def test_run():
    checks = HealthChecks()
    assert checks.last_checked is None
    checks.run()
    assert checks.last_checked is not None


@pytest.mark.django_db
def test_run_cached():
    checks = HealthChecks()
    assert checks.last_checked is None
    checks.run()
    assert checks.last_checked is not None
    last_check = checks.last_checked
    checks.run()
    assert last_check == checks.last_checked


@pytest.mark.django_db
def test_failed():
    checks = HealthChecks()
    messages = checks.failed()
    assert len(messages) > 0


@pytest.mark.django_db
def test_dict():
    checks = HealthChecks()
    request = RequestFactory().get(path=reverse(viewname="health-check"))
    data = checks.to_dict(request.build_absolute_uri())
    assert "status" in data
    assert "datetime" in data
    assert "serviceName" in data


@pytest.mark.django_db
def test_dict_show_dependencies():
    checks = HealthChecks()
    request = RequestFactory().get(path=reverse(viewname="health-check"))
    data = checks.to_dict(request.build_absolute_uri(), show_dependencies=True)
    assert "dependencies" in data


@pytest.mark.django_db
def test_dict_down():
    checks = HealthChecks()
    request = RequestFactory().get(path=reverse(viewname="health-check"))
    data = checks.to_dict(request.build_absolute_uri())
    assert data["status"] == Status.DOWN.value


@override_settings(HEALTH_CHECK_CRITICAL=[])
def test_sqs_not_critical():
    sqs = SQS()
    sqs.check()

    assert sqs.status == Status.DEGRADED


def test_sqs_critical():
    sqs = SQS()
    sqs.check()

    assert sqs.status == Status.DOWN


@pytest.mark.django_db
def test_database():
    database = PostgreSQL()
    database.check()

    assert database.status == Status.OK


def test_email():
    email = Email()
    email.check()

    assert email.status == Status.OK
