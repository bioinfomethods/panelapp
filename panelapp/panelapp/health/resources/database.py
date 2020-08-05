import logging

from django.conf import settings
from django.db import (
    OperationalError,
    connection,
)

from panelapp.health.enums import (
    ResourceType,
    Status,
)
from panelapp.health.resources.base import Resource

LOGGER = logging.getLogger(__name__)


class PostgreSQL(Resource):
    def __init__(self):
        self.name = "Database"
        self.connection_type = "OTHER"
        self.resource_type = ResourceType.DATASTORE

        self.is_configured = True
        self.url = settings.DATABASE_URL

        super(PostgreSQL, self).__init__()

    def check(self):
        status = (
            Status.DOWN
            if (self.name.lower() in getattr(settings, "HEALTH_CHECK_CRITICAL", []))
            else Status.DEGRADED
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                status = Status.OK
        except OperationalError as err:
            LOGGER.error(err, exc_info=True)

        self.status = status
        return self.status


resource = PostgreSQL
