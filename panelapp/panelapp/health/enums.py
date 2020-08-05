from enum import Enum


class Status(Enum):
    """Status of the application and dependencies.

    Doesn't strictly follow GelReportModels' HealthCheck, has two extra values:
    - DEGRADED - if application can function, bust some functionality is affected
    - NOT_CONFIGURED - either uses default values or values aren't set

    You can compare statuses as well, the order determined in `STATUS_ORDER`.
    The higher the index in that order, the less affected the app is.
    """

    OK = "OK"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"
    NOT_CONFIGURED = "NOT_CONFIGURED"

    def _get_order_index(self, other):
        """Order based on index in the _STATUS_ORDER"""

        return STATUS_ORDER.index(self), STATUS_ORDER.index(other)

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            si, oi = self._get_order_index(other)
            return si >= oi
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            si, oi = self._get_order_index(other)
            return si > oi
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            si, oi = self._get_order_index(other)
            return si <= oi
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            si, oi = self._get_order_index(other)
            return si < oi
        return NotImplemented


STATUS_ORDER = [Status.DOWN, Status.DEGRADED, Status.NOT_CONFIGURED, Status.OK]


class ResourceType(Enum):
    API = "API"
    DATASTORE = "DATASTORE"
