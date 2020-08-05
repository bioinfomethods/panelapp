import logging

from django.conf import settings
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import permission_classes
from rest_framework.views import APIView

from panelapp.health.enums import Status
from panelapp.health.health_check_serializers import HealthCheckSerializer
from panelapp.health.health_checks import checks as health_checks

LOGGER = logging.getLogger(__name__)


def ping(_):
    pong = {"ping": "pong"}
    return JsonResponse(pong)


def error(_):
    LOGGER.info("hello info", extra={"extra_item": "yes"})
    LOGGER.error("hello error", extra={"extra_item": "yes"})
    LOGGER.debug("hello debug", extra={"extra_item": "yes"})
    LOGGER.warn("hello warn", extra={"extra_item": "yes"})
    try:
        assert False
    except Exception as e:
        LOGGER.exception("exception message", exc_info=True)

    return JsonResponse({"error": "dummy error"}, status=500)


@permission_classes((permissions.AllowAny,))
class HealthCheck(APIView):
    serializer = HealthCheckSerializer

    def get(self, request):
        data = health_checks.to_dict(
            request.build_absolute_uri(),
            show_dependencies=self.display_extra,
            skip_resources=self.skip_resources,
        )
        result = self.serializer(data=data)

        if result.is_valid(raise_exception=True):
            if result.data["status"] == Status.DOWN.value:
                return JsonResponse(result.data, status=503)

            return JsonResponse(result.data)

    @property
    def display_extra(self):
        token = self.request.GET.get("token")
        return token and token == settings.HEALTH_CHECK_TOKEN

    @property
    def skip_resources(self):
        skip_resources = self.request.GET.get("skip")
        return skip_resources.lower().split(",") if skip_resources else []
