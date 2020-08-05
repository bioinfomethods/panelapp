import logging

from django.conf import settings
from django.core import mail

from panelapp.health.enums import (
    ResourceType,
    Status,
)
from panelapp.health.resources.base import Resource

LOGGER = logging.getLogger(__name__)


class Email(Resource):
    def __init__(self):
        self.name = "Email"
        self.connection_type = "OTHER"
        self.resource_type = ResourceType.DATASTORE

        self.is_configured = True
        self.url = "email"

        super(Email, self).__init__()

    def check(self):
        status = (
            Status.DOWN
            if (self.name.lower() in getattr(settings, "HEALTH_CHECK_CRITICAL", []))
            else Status.DEGRADED
        )

        try:
            connection = mail.get_connection()
            connection.open()
            status = Status.OK
        except Exception as err:
            LOGGER.error(err)

        self.status = status
        return self.status


resource = Email
