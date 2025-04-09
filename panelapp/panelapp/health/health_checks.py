import logging
from importlib import import_module
from time import time

from django.conf import settings
from django.utils import timezone

from panelapp.health.resources.base import Resource

from .enums import (
    ResourceType,
    Status,
)

LOGGER = logging.getLogger(__name__)


class HealthChecks(object):
    @staticmethod
    def get_module(name):
        resource = None

        try:
            package_name = "panelapp.health.resources.{}".format(name)
            resource_class = import_module(package_name).resource
            if issubclass(resource_class, Resource):
                resource = resource_class()
            else:
                resource = None
        except ImportError as e:
            LOGGER.error(e)

        return resource

    def __init__(self):
        self.resources = []
        self.last_checked = None

        modules = {}  # to avoid duplicates
        for name in settings.HEALTH_CHECKS:
            resource = HealthChecks.get_module(name)
            if resource:
                modules[resource.__class__.__name__] = resource

        self.resources = list(modules.values())

    def run(self):
        """Run all checks (at the moment sequentially) and update their states

        TODO when this is moved to Py3 implement parallel execution as all
             of them can be run independently.
        """
        if (
            self.last_checked
            and time() - self.last_checked < settings.HEALTH_CHECK_CACHE_SECONDS
        ):
            LOGGER.debug("Not running health check, using cached data")
            return

        for res in self.resources:
            res.check()

        self.last_checked = time()

    def failed(self):
        """Convert and return any failed components"""

        self.run()

        return [str(res) for res in self.resources if not res.ok]

    def to_dict(self, request_url, show_dependencies=False, skip_resources=None):
        """Convert to Serializer compatible object (for APIv2)"""

        self.run()
        skip_resources = skip_resources or []

        global_status = Status.OK

        dependencies = {"apis": [], "datastores": []}
        unavailable_components = []
        component_names = []

        for resource in self.resources:
            component_names.append(resource.name)
            if resource.name.lower() in skip_resources:
                continue
            resource_type = resource.resource_type
            if resource_type == ResourceType.API:
                dependencies["apis"].append(resource.to_dict())
            elif resource_type == ResourceType.DATASTORE:
                dependencies["datastores"].append(resource.to_dict())

            if resource.status is not Status.OK:
                unavailable_components.append(resource.name)

            if resource.status < global_status:
                global_status = resource.status

        data = {
            "status": global_status.value,
            "datetime": timezone.now(),
            "requestUrl": request_url,
            "serviceName": settings.HEALTH_CHECK_SERVICE_NAME,
            "components": component_names,
        }

        if global_status in [Status.DOWN, Status.DEGRADED, Status.NOT_CONFIGURED]:
            data["unavailableComponents"] = unavailable_components

        if show_dependencies:
            data["dependencies"] = dependencies

        return data


checks = HealthChecks()
