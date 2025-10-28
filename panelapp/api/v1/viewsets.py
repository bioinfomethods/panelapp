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
from math import ceil

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from panels.models import GenePanelSnapshot
from panels.models import GenePanelEntrySnapshot
from panels.models import HistoricalSnapshot
from panels.models import STR
from panels.models import Region
from panels.models import Activity
from panels.models import Gene
from panels.models import Tag
from panels.models import Evaluation
from panels.models import Comment
from django import forms
from django.db.models import Q
from django.db.models import ObjectDoesNotExist
from django.db.models import Value
from django.db import models
from django.utils.functional import cached_property
from django_filters import rest_framework as filters
from .serializers import PanelSerializer
from .serializers import ActivitySerializer
from .serializers import GeneSerializer
from .serializers import STRSerializer
from .serializers import EvaluationSerializer
from .serializers import RegionSerializer
from .serializers import EntitySerializer
from .serializers import HistoricalSnapshotSerializer
from .serializers import GeneAddSerializer
from .serializers import GeneReviewSerializer
from django.http import Http404
from rest_framework.exceptions import APIException
from panelapp.settings.base import REST_FRAMEWORK
from api.permissions import IsVerifiedReviewerOrReadOnly
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

class ReadOnlyListViewset(
    viewsets.mixins.RetrieveModelMixin,
    viewsets.mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    pass


CONFIDENCE_CHOICES = ((3, "Green"), (2, "Amber"), (1, "Red"), (0, "No List"))


class Http400(Exception):
    pass


class NumberChoices(filters.ChoiceFilter, filters.NumberFilter):
    pass


class EntityFilter(filters.FilterSet):
    entity_name = filters.BaseInFilter(field_name="entity_name", lookup_expr="in")
    confidence_level = NumberChoices(
        method="filter_confidence_level",
        choices=CONFIDENCE_CHOICES,
        help_text="Filter by confidence level: 0, 1, 2, 3",
    )  # FIXME should be custom
    version = filters.CharFilter(method="version_lookup", help_text="Panel version")
    tags = filters.BaseInFilter(field_name="tags__name", lookup_expr="in")

    class Meta:
        fields = ["entity_name", "confidence_level", "tags"]

    def filter_confidence_level(self, queryset, name, value):
        field = "saved_gel_status"
        try:
            value = int(value)
            if value >= 3:
                value = 3
                field = field + "__gte"
        except ValueError:
            raise APIException(
                detail="Incorrect confidence level", code="incorrect_confidence_level"
            )

        return queryset.filter(**{field: value})

    def version_lookup(self, queryset, name, value):
        try:
            major, minor = value.split(".")
        except ValueError:
            raise APIException(
                detail="Incorrect version supplied", code="incorrect_version"
            )

        return queryset.filter(panel__major_version=major, panel__minor_version=minor)


class PanelsFilter(filters.FilterSet):
    type = filters.BaseInFilter(field_name="panel__types__slug", lookup_expr="in")

    class Meta:
        fields = ["type"]


class PanelsViewSet(ReadOnlyListViewset):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_value_regex = "[^/]+"
    serializer_class = PanelSerializer
    filter_class = PanelsFilter

    def get_serializer(self, *args, **kwargs):
        if (
            self.action == "retrieve"
            and self.request.query_params.get("exclude_entities") != "True"
        ):
            kwargs["include_entities"] = True
        return super().get_serializer(*args, **kwargs)

    def get_queryset(self):
        retired = self.request.query_params.get("retired", False)
        name = self.request.query_params.get("name", None)
        return GenePanelSnapshot.objects.get_active_annotated(all=retired, name=name)

    def get_object(self):
        version = self.request.query_params.get("version", None)
        param = {}
        if version:
            param.update({'all': True, 'deleted': True, 'internal': True})
        obj = GenePanelSnapshot.objects.get_active_annotated(
            name=self.kwargs["pk"], **param
        ).first()

        if obj:
            return obj

        raise Http404

    def retrieve(self, request, *args, **kwargs):
        """Get individual Panel data

        In addition to the model fields this endpoint also returns `genes`, `strs`, `regions` associated with this panel.

        Additional parameters:

        ?version=1.1 - get a specific version for this panel
        """
        version = self.request.query_params.get("version", None)
        if version:
            try:
                major_version, minor_version = version.split(".")
            except ValueError:
                raise APIException(
                    detail="Incorrect version supplied", code="incorrect_version"
                )

            panel_id = self.kwargs["pk"]
            id_kwarg = 'panel_id' if panel_id.isdigit() else 'panel__old_pk'
            filter_kwargs = {
                id_kwarg: panel_id
            }

            latest = GenePanelSnapshot.objects.filter(**filter_kwargs).first()

            if str(latest.major_version) == major_version and str(latest.minor_version) == minor_version:
                return super().retrieve(request, *args, **kwargs)

            filter_kwargs['major_version'] = major_version
            filter_kwargs['minor_version'] = minor_version

            snap = HistoricalSnapshot.objects.filter(**filter_kwargs).first()
            if snap:
                json = snap.to_api_1()
                return Response(json)
            else:
                raise Http404
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True)
    def versions(self, request, pk=None):
        versions = GenePanelSnapshot.objects.get_panel_snapshots(pk)

        page = self.paginate_queryset(versions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def activities(self, request, pk=None):
        if request.user.is_authenticated and request.user.reviewer.is_GEL():
            activities = Activity.objects.visible_to_gel()
        else:
            activities = Activity.objects.visible_to_public()

        activities = activities.filter(Q(panel_id=pk) | Q(extra_data__panel_id=pk))

        return Response(ActivitySerializer(activities, many=True).data)


class ActivityViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = ActivitySerializer

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.reviewer.is_GEL():
            return Activity.objects.visible_to_gel()
        else:
            return Activity.objects.visible_to_public()


class EntityViewSet(viewsets.mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = "entity_name"
    lookup_url_kwarg = "entity_name"
    recent_version_only = False

    def filter_list(self, obj):
        entity_name = self.request.query_params.get("entity_name")
        confidence_level = self.request.query_params.get("confidence_level")
        tags = self.request.query_params.get("tags")

        list_filters = []
        if entity_name:
            list_filters.append(obj["entity_name"] in entity_name.split(","))
        if confidence_level:
            list_filters.append(obj["confidence_level"] == confidence_level)
        if tags:
            for tag in tags.split(","):
                list_filters.append(tag in obj["tags"])
        if list_filters:
            return all(list_filters)
        else:
            return True

    def paginate(self, obj):
        count = len(obj.data["genes"])
        start = 0
        finish = REST_FRAMEWORK['PAGE_SIZE']
        page = self.request.query_params.get("page", None)
        response = {
            "count": count,
            "next": None,
            "previous": None,
            "results": [],
        }
        max_pages = ceil(count / finish)

        if max_pages > 1:
            if page:
                page = int(page)
                start = (page - 1) * finish
                finish = page * finish
                next_page = (page + 1) if page + 1 <= max_pages else None
                previous_page = (page - 1) if page - 1 >= 1 else None
                if next_page:
                    response["next"] = self.request.build_absolute_uri().replace(
                        "&page=" + str(page), "&page=" + str(next_page)
                    )
                if previous_page:
                    response["previous"] = self.request.build_absolute_uri().replace(
                        "&page=" + str(page), "&page=" + str(previous_page)
                    )

            else:
                response["next"] = self.request.build_absolute_uri() + "&page=2"

        collection = obj.data[self.lookup_collection]

        collection = list(filter(self.filter_list, collection))

        for gene in collection[start:finish]:
            response["results"].append(gene)

        response["count"] = len(collection)
        return response

    def list(self, request, *args, **kwargs):
        version = self.request.query_params.get("version", None)
        if version:
            try:
                major_version, minor_version = version.split(".")
            except ValueError:
                raise APIException(
                    detail="Incorrect version supplied", code="incorrect_version"
                )

            panel_id = self.kwargs["panel_pk"]
            id_kwarg = 'panel_id' if panel_id.isdigit() else 'panel__old_pk'
            filter_kwargs = {
                id_kwarg: panel_id
            }

            latest = GenePanelSnapshot.objects.filter(**filter_kwargs).first()

            if str(latest.major_version) == major_version and str(latest.minor_version) == minor_version:
                return super().list(request, *args, **kwargs)

            if self.recent_version_only:
                raise Http400('Endpoint doesnt support version parameter')

            obj = HistoricalSnapshot.objects.filter(**filter_kwargs).filter(
                major_version=major_version,
                minor_version=minor_version,
            ).first()

            if obj:
                response = self.paginate(obj)
                return Response(response)
            else:
                raise Http404
        else:
            return super().list(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
        except Http400 as e:
            response = Response({"error": str(e)}, status=400)
            response = self.finalize_response(request, response, *args, **kwargs)
        return response

    def get_panel(self):
        obj = GenePanelSnapshot.objects.get_active_annotated(
            all=True, internal=True, deleted=True, name=self.kwargs["panel_pk"]
        ).first()

        if not obj:
            raise Http404

        version = self.request.query_params.get("version")
        if version:
            try:
                major_version, minor_version = version.split(".")
                if str(obj.major_version) == major_version and str(obj.minor_version) == minor_version:
                    return obj
                else:
                    raise Http400('Endpoint doesnt support version parameter')
            except ValueError:
                raise APIException(
                    detail="Incorrect version supplied", code="incorrect_version"
                )
        else:
            return obj


class GeneViewSet(EntityViewSet, viewsets.mixins.CreateModelMixin):
    permission_classes = (IsVerifiedReviewerOrReadOnly,)
    serializer_class = GeneSerializer
    filter_class = EntityFilter
    lookup_collection = "genes"

    def get_queryset(self):
        return self.get_panel().get_all_genes.prefetch_related("evidence", "tags")

    def get_serializer_class(self):
        """Use GeneAddSerializer for POST, GeneSerializer for GET"""
        if self.action == 'create':
            return GeneAddSerializer
        return GeneSerializer

    def get_serializer_context(self):
        """Add panel to context for validation during POST"""
        context = super().get_serializer_context()
        if self.action == 'create':
            context['panel'] = self.get_panel()
        return context

    @extend_schema(
        operation_id='panels_genes_create',
        summary='Add gene to panel',
        description="""
        Add an existing gene to a panel with minimal metadata, WITHOUT creating a review.

        **Required fields:**
        - gene_symbol: Must exist in the gene reference database
        - moi: Mode of inheritance
        - sources: At least one evidence source

        **Optional fields:**
        - penetrance, mode_of_pathogenicity, publications, phenotypes
        - transcript, tags (GEL users only)

        **Behavior:**
        - GEL users: Increments panel version, gene not flagged, can assign tags/transcript
        - Non-GEL verified reviewers: No version increment, gene flagged, cannot assign tags/transcript
        - Creates GenePanelEntrySnapshot and Evidence records
        - Does NOT create Evaluation (no review)
        """,
        request=GeneAddSerializer,
        responses={
            201: GeneSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Minimal gene addition',
                value={
                    'gene_symbol': 'DMD',
                    'moi': 'X-LINKED: hemizygous mutation in males, biallelic mutations in females',
                    'sources': ['Expert Review', 'Literature']
                },
                request_only=True,
            ),
            OpenApiExample(
                'Gene addition with metadata',
                value={
                    'gene_symbol': 'CFTR',
                    'moi': 'BIALLELIC, autosomal or pseudoautosomal',
                    'sources': ['Expert Review'],
                    'penetrance': 'Complete',
                    'mode_of_pathogenicity': 'Loss-of-function variants (as defined in pop up message) DO NOT cause this phenotype - please provide details in the comments',
                    'publications': ['12345678'],
                    'phenotypes': ['Cystic fibrosis']
                },
                request_only=True,
            ),
        ],
        tags=['Panels'],
    )
    def create(self, request, *args, **kwargs):
        """Add a gene to the panel"""
        panel = self.get_panel()

        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Prepare data for panel.add_gene()
        data = serializer.validated_data.copy()
        gene_symbol = data.pop('gene_symbol')

        # Convert tag IDs to Tag queryset (if provided)
        if 'tags' in data and data['tags']:
            data['tags'] = Tag.objects.filter(pk__in=data['tags'])

        # Determine if version should be incremented
        increment_version = request.user.is_authenticated and request.user.reviewer.is_GEL()

        # Add the gene using existing business logic
        gene_entry = panel.add_gene(
            user=request.user,
            gene_symbol=gene_symbol,
            gene_data=data,
            increment_version=increment_version,
        )

        if gene_entry is False:
            return Response(
                {'gene_symbol': f"Gene '{gene_symbol}' already exists in this panel"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Refetch the gene entry with proper annotations for serialization
        gene_entry_annotated = GenePanelEntrySnapshot.objects.filter(
            pk=gene_entry.pk
        ).annotate(
            entity_type=Value("gene", output_field=models.CharField()),
            entity_name=models.F("gene_core__gene_symbol"),
        ).first()

        # Return the created gene entry
        response_serializer = GeneSerializer(gene_entry_annotated)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class GeneEvaluationsViewSet(EntityViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = EvaluationSerializer
    recent_version_only = True

    def get_queryset(self):
        panel = self.get_panel()
        try:
            gene = panel.get_gene(self.kwargs["gene_entity_name"])
            return gene.evaluation.all()
        except ObjectDoesNotExist:
            raise Http404


class STRViewSet(EntityViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = STRSerializer
    filter_class = EntityFilter
    lookup_collection = "strs"

    def get_queryset(self):
        return self.get_panel().get_all_strs.prefetch_related("evidence", "tags")


class STREvaluationsViewSet(EntityViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = EvaluationSerializer
    recent_version_only = True

    def get_queryset(self):
        panel = self.get_panel()
        try:
            str_item = panel.get_str(self.kwargs["str_entity_name"])
            return str_item.evaluation.all()
        except ObjectDoesNotExist:
            raise Http404


class RegionViewSet(EntityViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    serializer_class = RegionSerializer
    filter_class = EntityFilter
    lookup_collection = "regions"

    def get_queryset(self):
        return self.get_panel().get_all_regions.prefetch_related("evidence", "tags")


class RegionEvaluationsViewSet(EntityViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = EvaluationSerializer
    recent_version_only = True

    def get_queryset(self):
        panel = self.get_panel()
        try:
            region = panel.get_region(self.kwargs["region_entity_name"])
            return region.evaluation.all()
        except ObjectDoesNotExist:
            raise Http404


class EntitySearchFilter(filters.FilterSet):
    type = filters.BaseInFilter(
        field_name="panel__panel__types__slug", lookup_expr="in"
    )
    tags = filters.BaseInFilter(field_name="tags__name", lookup_expr="in")
    entity_name = filters.BaseInFilter(field_name="entity_name", lookup_expr="in")

    class Meta:
        fields = ["type", "tags", "entity_name"]


class EntitySearch(ReadOnlyListViewset):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    lookup_field = "entity_name"
    lookup_url_kwarg = "entity_name"
    filter_class = EntitySearchFilter

    @property
    def active_snapshot_ids(self):
        panel_names = self.request.query_params.get("panel_name", "")
        if panel_names:
            all_panels = (
                GenePanelSnapshot.objects.get_active_annotated()
                .filter(panel__name__in=panel_names.split(","))
                .values_list("pk", flat=True)
            )
        else:
            all_panels = GenePanelSnapshot.objects.get_active_annotated().values_list(
                "pk", flat=True
            )

        return list(all_panels)

    @property
    def qs_filters(self):
        filters = {}

        if self.kwargs.get("entity_name"):
            filters["entity_name__in"] = self.kwargs["entity_name"].split(",")
        elif self.request.query_params.get("entity_name"):
            filters["entity_name__in"] = self.request.query_params["entity_name"].split(
                ","
            )

        if self.request.query_params.get("type"):
            filters["panel__panel__types__slug__in"] = self.request.query_params[
                "type"
            ].split(",")

        if self.request.query_params.get("tags"):
            filters["tags__name__in"] = self.request.query_params["tags"].split(",")

        return filters


class GeneSearchViewSet(EntitySearch):
    """Search Genes"""

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = GeneSerializer

    def get_queryset(self):
        filters = {"pks": self.active_snapshot_ids}

        return GenePanelEntrySnapshot.objects.get_active(**filters).filter(
            **self.qs_filters
        )

    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class STRSearchViewSet(EntitySearch):
    """Search STRs"""

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = STRSerializer

    def get_queryset(self):
        filters = {"pks": self.active_snapshot_ids}

        return STR.objects.get_active(**filters).filter(**self.qs_filters)

    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RegionSearchViewSet(EntitySearch):
    """Search Regions"""

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = RegionSerializer

    def get_queryset(self):
        filters = {"pks": self.active_snapshot_ids}

        return Region.objects.get_active(**filters).filter(**self.qs_filters)

    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class EntitySearchViewSet(EntitySearch):
    """Search Entities"""

    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    serializer_class = EntitySerializer
    filter_class = EntitySearchFilter

    @cached_property
    def snapshot_ids(self):
        if self.request.query_params.get("panel_name"):
            panel_names = self.request.query_params.get("panel_name").split(",")
        else:
            panel_names = None

        if panel_names:
            all_panels = GenePanelSnapshot.objects.get_active_annotated().filter(
                panel__name__in=panel_names
            )
        else:
            all_panels = GenePanelSnapshot.objects.get_active_annotated()

        return all_panels.values_list("pk", flat=True)

    def get_queryset(self):
        filters = {}

        if self.kwargs.get("entity_name"):
            filters["entity_name__in"] = self.kwargs["entity_name"].split(",")
        elif self.request.query_params.get("entity_name"):
            filters["entity_name__in"] = self.request.query_params["entity_name"].split(
                ","
            )

        if self.request.query_params.get("type"):
            filters["panel__panel__types__slug__in"] = self.request.query_params[
                "type"
            ].split(",")

        if self.request.query_params.get("tags"):
            filters["tag__name__in"] = self.request.query_params["tags"].split(",")

        active_genes = GenePanelEntrySnapshot.objects.get_active_slim(
            pks=self.snapshot_ids
        )
        genes = active_genes.filter(**filters)

        active_strs = STR.objects.get_active_slim(pks=self.snapshot_ids)
        strs = active_strs.filter(**filters)

        active_regions = Region.objects.get_active_slim(pks=self.snapshot_ids)
        regions = active_regions.filter(**filters)

        return (
            strs.union(genes).union(regions).values("entity_name", "entity_type", "pk")
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)

        genes = GenePanelEntrySnapshot.objects.get_active().filter(
            pk__in=[e.get("pk") for e in page if e.get("entity_type") == "gene"]
        )
        strs = STR.objects.get_active().filter(
            pk__in=[e.get("pk") for e in page if e.get("entity_type") == "str"]
        )
        regions = Region.objects.get_active().filter(
            pk__in=[e.get("pk") for e in page if e.get("entity_type") == "region"]
        )

        serializer = self.get_serializer(
            list(genes) + list(strs) + list(regions), many=True
        )

        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class SignedOffPanelViewSet(ReadOnlyListViewset):
    serializer_class = HistoricalSnapshotSerializer

    def get_queryset(self):
        return HistoricalSnapshot.objects.filter(signed_off_date__isnull=False)

    def retrieve(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        snap = self.get_queryset().filter(panel__pk=pk).first()
        if snap:
            json = snap.to_api_1()
            return Response(json)
        else:
            raise Http404


class GeneReviewViewSet(viewsets.GenericViewSet, viewsets.mixins.CreateModelMixin):
    """
    ViewSet for submitting reviews/evaluations for genes in panels.

    POST /api/v1/panels/{panel_id}/genes/{gene_symbol}/reviews/ - Submit review

    Only supports POST (create). Does not support GET/PUT/DELETE.
    Requires verified reviewer permission.
    """

    permission_classes = (IsVerifiedReviewerOrReadOnly,)
    serializer_class = GeneReviewSerializer

    @extend_schema(
        operation_id='panels_genes_reviews_create',
        summary='Submit review for gene',
        description="""
        Submit a review/evaluation for a gene that's already in the panel.

        **All fields are optional, but at least one must be provided:**
        - rating: GREEN, AMBER, or RED
        - comments: Review comments
        - moi: Reviewer's opinion on mode of inheritance
        - mode_of_pathogenicity
        - publications: Supporting PMIDs
        - phenotypes: Associated phenotypes
        - current_diagnostic: Boolean
        - clinically_relevant: Boolean (primarily for STRs)

        **Behavior:**
        - Creates Evaluation record linked to the gene entry
        - Creates Comment record if comments provided
        - Does NOT modify GenePanelEntrySnapshot metadata
        - Does NOT increment panel version
        - Multiple reviews allowed (same or different users)
        """,
        parameters=[
            OpenApiParameter(
                name='panel_pk',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Panel ID or old_pk'
            ),
            OpenApiParameter(
                name='gene_symbol',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='Gene symbol'
            ),
        ],
        request=GeneReviewSerializer,
        responses={
            201: EvaluationSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Simple review with rating',
                value={
                    'rating': 'GREEN',
                    'comments': 'Well-established gene-disease association for Duchenne muscular dystrophy'
                },
                request_only=True,
            ),
            OpenApiExample(
                'Detailed review',
                value={
                    'rating': 'GREEN',
                    'comments': 'Strong evidence from multiple sources for role in primary ciliary dyskinesia',
                    'moi': 'BIALLELIC, autosomal or pseudoautosomal',
                    'mode_of_pathogenicity': 'Loss-of-function variants (as defined in pop up message) DO NOT cause this phenotype - please provide details in the comments',
                    'publications': ['87654321', '11223344'],
                    'phenotypes': ['Primary ciliary dyskinesia', 'Kartagener syndrome'],
                    'current_diagnostic': True
                },
                request_only=True,
            ),
        ],
        tags=['Panels'],
    )
    def create(self, request, *args, **kwargs):
        """
        Submit a review for the gene.

        This creates an Evaluation record linked to the existing
        GenePanelEntrySnapshot. Does NOT modify the gene entry's metadata.
        Does NOT increment panel version.
        """
        gene_entry, panel = self.get_gene_entry()

        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Create Evaluation record
        evaluation = Evaluation.objects.create(
            user=request.user,
            rating=data.get('rating', ''),
            mode_of_pathogenicity=data.get('mode_of_pathogenicity', ''),
            phenotypes=data.get('phenotypes'),
            publications=data.get('publications'),
            moi=data.get('moi', ''),
            current_diagnostic=data.get('current_diagnostic', False),
            clinically_relevant=data.get('clinically_relevant', False),
            version=panel.version,
        )

        # Add comment if provided
        if data.get('comments'):
            comment = Comment.objects.create(user=request.user, comment=data['comments'])
            evaluation.comments.add(comment)

        # Link evaluation to gene entry
        gene_entry.evaluation.add(evaluation)

        # Return the created evaluation
        response_serializer = EvaluationSerializer(evaluation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def get_gene_entry(self):
        """
        Get the gene entry from panel.
        Returns (gene_entry, panel) tuple.
        Raises 404 if panel or gene not found.
        """
        panel_id = self.kwargs['panel_pk']
        gene_symbol = self.kwargs['gene_entity_name']

        # Get panel
        panel = GenePanelSnapshot.objects.get_active_annotated(name=panel_id).first()

        if not panel:
            raise Http404(f"Panel '{panel_id}' not found")

        # Get gene entry in panel
        try:
            gene_entry = panel.get_gene(gene_symbol)
        except GenePanelEntrySnapshot.DoesNotExist:
            raise Http404(f"Gene '{gene_symbol}' not found in panel '{panel_id}'")

        return gene_entry, panel
