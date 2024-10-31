import re
from unittest import mock

import pytest
from django.test import override_settings

from panelapp.content_security_policy import (
    aws,
    default,
)


@pytest.mark.django_db
@override_settings(CONTENT_SECURITY_POLICY=default())
@mock.patch("os.urandom", lambda _: b"wm1W[\x01\xd9\x8e\xce;\xe9\xc4M\xfa\xad\x91")
def test_default(client):
    response = client.get("/")

    assert "Content-Security-Policy" in response.headers.keys()
    # Directives are unpredictably ordered
    policy = set(response.headers["Content-Security-Policy"].split("; "))
    assert policy == {
        "default-src 'self' 'nonce-d20xV1sB2Y7OO+nETfqtkQ=='",
        "frame-ancestors 'self'",
        "form-action 'self'",
    }


@pytest.mark.django_db
@override_settings(CONTENT_SECURITY_POLICY=aws("static/url", "media/url"))
@mock.patch("os.urandom", lambda _: b"wm1W[\x01\xd9\x8e\xce;\xe9\xc4M\xfa\xad\x91")
def test_aws(client):
    response = client.get("/")

    assert "Content-Security-Policy" in response.headers.keys()
    # Directives are unpredictably ordered
    policy = set(response.headers["Content-Security-Policy"].split("; "))
    assert policy == {
        "default-src 'self' 'nonce-d20xV1sB2Y7OO+nETfqtkQ==' static/url media/url",
        "frame-ancestors 'self'",
        "form-action 'self'",
    }
