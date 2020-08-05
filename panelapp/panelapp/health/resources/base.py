import logging

import requests
from django.conf import settings
from django.core.checks import ERROR

from panelapp.health.enums import (
    ResourceType,
    Status,
)

LOGGER = logging.getLogger(__name__)


class Resource:
    """Abstract class for the resource"""

    name = ""
    description = ""
    is_configured = False
    resource_type = None
    failed_status = Status.DOWN
    url = None
    health_path = ""
    level = ERROR
    connection_type = None
    status = None
    check_time = None
    affected = list()  # list of affected parts of code (user facing)

    def __init__(self, *args, **kwargs):
        if not self.is_configured:
            self.status = Status.NOT_CONFIGURED
        else:
            self.validate_setup()

    def __str__(self):
        return (
            f"[Health] {self.name}({self.connection_type}) Status: {self.status.value}"
        )

    def to_dict(self, *args, **kwargs):
        additional_properties = {}

        res = {
            "status": self.status.value,
            "type": self.connection_type,
            "description": self.name,
            "url": [self.safe_url] if self.url else [],
        }

        if self.health_path:
            additional_properties["healthPath"] = self.health_path

        if not self.ok and self.affected:
            additional_properties["affected"] = ",".join(self.affected)

        if additional_properties:
            res["additionalProperties"] = additional_properties

        return res

    @property
    def ok(self):
        return self.status == Status.OK

    def validate_setup(self):
        """Check if child classes are configured"""

        assert self.name
        assert self.resource_type
        assert self.url
        assert self.level
        assert self.connection_type

    def check(self):
        raise NotImplementedError()

    @property
    def safe_url(self):
        """Return URL without auth part"""

        if self.url:
            return self.url.split("@")[1] if "@" in self.url else self.url


class SimpleHTTPResource(Resource):
    """Abstract REST Resource check"""

    failed_status = Status.DEGRADED
    health_path = ""  # relative path to the health check endpoint
    method = "GET"
    resource_type = ResourceType.API

    def __init__(self, *args, **kwargs):
        self.connection_type = "REST"
        super(SimpleHTTPResource, self).__init__(*args, **kwargs)

    @property
    def headers(self):
        return {}

    @property
    def request_params(self):
        return {}

    def check(self):
        if not self.is_configured:
            # Don't run check if it's not configured
            return

        if self.name.lower() in getattr(settings, "HEALTH_CHECK_CRITICAL", []):
            self.failed_status = Status.DOWN

        _status = self.failed_status
        try:
            url = "{}{}".format(self.url, self.health_path)
            response = requests.request(
                self.method,
                url,
                headers=self.headers,
                timeout=settings.HEALTH_CHECK_TIMEOUT,
                **self.request_params,
            )
            if response.ok:
                _status = Status.OK
            post_check_status = self.post_check(response)
            if post_check_status:
                _status = post_check_status
        except Exception as error:
            LOGGER.error(error)

        self.status = _status
        return self.status

    def post_check(self, response):
        """Check the response body and return new status

        :param response: `requests` Response object
        :return: Status value or None
        """

        return None
