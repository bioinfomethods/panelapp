import logging

import boto3
from django.conf import settings

from panelapp.health.enums import (
    ResourceType,
    Status,
)
from panelapp.health.resources.base import Resource

LOGGER = logging.getLogger(__name__)


class SQS(Resource):
    def __init__(self):
        self.name = "SQS"
        self.connection_type = "OTHER"
        self.resource_type = ResourceType.DATASTORE

        self.is_configured = True
        self.url = settings.CELERY_BROKER_URL

        super(SQS, self).__init__()

    def check(self):
        status = (
            Status.DOWN
            if (self.name.lower() in getattr(settings, "HEALTH_CHECK_CRITICAL", []))
            else Status.DEGRADED
        )

        try:
            client_config = {
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                "region_name": settings.AWS_REGION,
            }
            if "localstack" in settings.CELERY_BROKER_URL:
                client_config["endpoint_url"] = settings.CELERY_BROKER_URL.replace(
                    "sqs", "http"
                )

            boto3.client("sqs", **client_config).get_queue_url(
                QueueName=settings.CELERY_TASK_DEFAULT_QUEUE
            )

            status = Status.OK
        except Exception as err:
            LOGGER.error(err, exc_info=True)

        self.status = status
        return self.status


resource = SQS
