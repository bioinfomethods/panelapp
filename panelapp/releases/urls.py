from django.urls import re_path

from releases.views import (
    release_create_view,
    release_deployment_status_view,
    release_deployment_view,
    release_detail_view,
    release_edit_view,
    release_list_view,
)
from releases.views.panels import (
    ReleasePanelsImportView,
    release_panels_export_view,
    release_panels_list_view,
)

app_name = "releases"

PK_PARAM = "(?P<pk>[0-9]+)"

urlpatterns = [
    re_path(
        r"^$",
        release_list_view,
        name="list",
    ),
    re_path(
        r"^create/$",
        release_create_view,
        name="create",
    ),
    re_path(
        rf"^{PK_PARAM}/$",
        release_detail_view,
        name="detail",
    ),
    re_path(
        rf"^{PK_PARAM}/edit/$",
        release_edit_view,
        name="edit",
    ),
    re_path(
        rf"^{PK_PARAM}/deployment/$",
        release_deployment_view,
        name="deployment",
    ),
    re_path(
        rf"^{PK_PARAM}/deployment/status/$",
        release_deployment_status_view,
        name="deployment-status",
    ),
    re_path(
        rf"^{PK_PARAM}/panels/$",
        release_panels_list_view,
        name="releasepanel-list",
    ),
    re_path(
        rf"^{PK_PARAM}/panels/import/$",
        ReleasePanelsImportView.as_view(),
        name="releasepanel-import",
    ),
    re_path(
        rf"^{PK_PARAM}/panels/export/$",
        release_panels_export_view,
        name="releasepanel-export",
    ),
]
