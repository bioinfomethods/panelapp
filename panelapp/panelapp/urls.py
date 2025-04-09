##
## Copyright (c) 2016-2019 Genomics England Ltd.
##
## This file is part of PanelApp
## (see https://panelapp.genomicsengland.co.uk).
##
## Licensed to the Apache Software Foundation (ASF) under one
## or more contributor license agreements.  See the NOTICE file
## distributed with this work for additional information
## regarding copyright ownership.  The ASF licenses this file
## to you under the Apache License, Version 2.0 (the
## "License"); you may not use this file except in compliance
## with the License.  You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing,
## software distributed under the License is distributed on an
## "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
## KIND, either express or implied.  See the License for the
## specific language governing permissions and limitations
## under the License.
##
"""panelapp URL Configuration

"""
from django.conf import settings
from django.contrib import admin
from django.urls import (
    include,
    path,
    re_path,
)
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .autocomplete import (
    GeneAutocomplete,
    SimpleAllPanelsAutocomplete,
    SimplePanelTypesAutocomplete,
    SimplePublicPanelsAutocomplete,
    SourceAutocomplete,
    TagsAutocomplete,
)
from .health.views.health_check_views import (
    HealthCheck,
    ping,
)
from .views import (
    Homepage,
    VersionView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="PanelApp API",
        default_version="v1",
        description="PanelApp API",
        terms_of_service="https://panelapp.genomicsengland.co.uk/policies/terms/",
        contact=openapi.Contact(email="panelapp@genomicsengland.co.uk"),
    ),
    patterns=[path("api/", include("api.urls"))],  # exclude old webservices
    validators=["flex", "ssv"],
    public=True,
    permission_classes=(permissions.AllowAny,),  # FIXME(Oleg) we need read only.
)


urlpatterns = [
    path("", Homepage.as_view(), name="home"),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("panels/", include("panels.urls", namespace="panels")),
    path("releases/", include("releases.urls", namespace="releases")),
    path("crowdsourcing/", include("v1rewrites.urls", namespace="v1rewrites")),
    re_path(
        r"^api/docs(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=None),
        name="schema-json",
    ),
    re_path(
        r"^api/docs/$",
        schema_view.with_ui("swagger", cache_timeout=None),
        name="schema-swagger-ui",
    ),
    path("api/", include("api.urls", namespace="api")),
    path("WebServices/", include("webservices.urls", namespace="webservices")),
    path("markdownx/", include("markdownx.urls")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("autocomplete/gene/", GeneAutocomplete.as_view(), name="autocomplete-gene"),
    path(
        "autocomplete/source/", SourceAutocomplete.as_view(), name="autocomplete-source"
    ),
    path("autocomplete/tags/", TagsAutocomplete.as_view(), name="autocomplete-tags"),
    path(
        "autocomplete/panels/simple/",
        SimplePublicPanelsAutocomplete.as_view(),
        name="autocomplete-simple-panels-public",
    ),
    path(
        "autocomplete/panels/all/",
        SimpleAllPanelsAutocomplete.as_view(),
        name="autocomplete-simple-panels-all",
    ),
    path(
        "autocomplete/panels/type/",
        SimplePanelTypesAutocomplete.as_view(),
        name="autocomplete-simple-panel-types",
    ),
    path("version/", VersionView.as_view(), name="version"),
    path("health/1/", HealthCheck.as_view(), name="health-check"),
    path("ping/1/", ping, name="ping"),
]

if settings.DEBUG:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns

    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
