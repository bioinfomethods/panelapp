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
from django.conf.urls import url
from django.views.generic import RedirectView

from .ajax_views import (
    ApproveEntityAjaxView,
    ApprovePanelAjaxView,
    ClearModeOfPathogenicityAjaxView,
    ClearPhoenotypesAjaxView,
    ClearPublicationsAjaxView,
    ClearSingleSourceAjaxView,
    ClearSourcesAjaxView,
    ClearTranscriptAjaxView,
    DeleteEntityAjaxView,
    DeleteEntityCommentAjaxView,
    DeleteEntityEvaluationAjaxView,
    DeletePanelAjaxView,
    GetEntityCommentFormAjaxView,
    RejectPanelAjaxView,
    SubmitEntityCommentFormAjaxView,
    UpdateEntityMOIAjaxView,
    UpdateEntityMOPAjaxView,
    UpdateEntityPhenotypesAjaxView,
    UpdateEntityPublicationsAjaxView,
    UpdateEntityRatingAjaxView,
    UpdateEntityTagsAjaxView,
)
from .enums import VALID_ENTITY_FORMAT
from .views import (
    ActivityListView,
    AdminUploadGenesView,
    AdminUploadPanelsView,
    AdminUploadReviewsView,
    AdminView,
    CompareGeneView,
    ComparePanelsView,
    CopyReviewsView,
    CreatePanelView,
    DownloadAllGenes,
    DownloadAllPanels,
    DownloadAllRegions,
    DownloadAllSTRs,
    DownloadPanelTSVView,
    DownloadPanelVersionTSVView,
    EntitiesListView,
    EntityDetailView,
    EntityReviewView,
    GeneDetailRedirectView,
    GenePanelSpanshotView,
    GenePanelView,
    MarkEntityReadyView,
    MarkGeneNotReadyView,
    OldCodeURLRedirect,
    PanelAddEntityView,
    PanelEditEntityView,
    PanelMarkNotReadyView,
    PanelsIndexView,
    PromotePanelView,
    RedirectGenesToEntities,
    UpdatePanelView,
)

app_name = "panels"

entity_types = "gene|str|region"
TYPE_PARAM = f"(?P<entity_type>({entity_types}))"
NAME_PARAM = f"(?P<entity_name>{VALID_ENTITY_FORMAT})"
PK_PARAM = "(?P<pk>[0-9]+)"
COMMENT_PK_PARAM = "(?P<comment_pk>[0-9]+)"

urlpatterns = [
    url(r"^$", PanelsIndexView.as_view(), name="index"),
    url(r"^compare/$", ComparePanelsView.as_view(), name="compare_panels_form"),
    url(
        r"^compare/(?P<panel_1_id>[0-9]+)/(?P<panel_2_id>[0-9]+)$",
        ComparePanelsView.as_view(),
        name="compare",
    ),
    url(
        r"^compare/(?P<panel_1_id>[0-9]+)/(?P<panel_2_id>[0-9]+)/(?P<gene_symbol>[\w\-]+)$",
        CompareGeneView.as_view(),
        name="compare_genes",
    ),
    url(
        r"^copy/(?P<panel_1_id>[0-9]+)/(?P<panel_2_id>[0-9]+)$",
        CopyReviewsView.as_view(),
        name="copy_reviews",
    ),
    url(rf"^{PK_PARAM}/$", GenePanelView.as_view(), name="detail"),
    url(rf"^{PK_PARAM}/update$", UpdatePanelView.as_view(), name="update"),
    url(rf"^{PK_PARAM}/promote$", PromotePanelView.as_view(), name="promote"),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/add$",
        PanelAddEntityView.as_view(),
        name="add_entity",
    ),
    url(rf"^{PK_PARAM}/delete$", DeletePanelAjaxView.as_view(), name="delete_panel"),
    url(rf"^{PK_PARAM}/reject$", RejectPanelAjaxView.as_view(), name="reject_panel"),
    url(
        rf"^{PK_PARAM}/approve$", ApprovePanelAjaxView.as_view(), name="approve_panel",
    ),
    url(
        rf"^{PK_PARAM}/download/(?P<categories>[0-4]+)/$",
        DownloadPanelTSVView.as_view(),
        name="download_panel_tsv",
    ),
    url(
        rf"^{PK_PARAM}/download_version/$",
        DownloadPanelVersionTSVView.as_view(),
        name="download_old_panel_tsv",
    ),
    url(
        rf"^{PK_PARAM}/{NAME_PARAM}/$",
        RedirectGenesToEntities.as_view(),
        name="redirect_previous_structure",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/$",
        GenePanelSpanshotView.as_view(),
        name="evaluation",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/edit$",
        PanelEditEntityView.as_view(),
        name="edit_entity",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/review$",
        EntityReviewView.as_view(),
        name="review_entity",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/mark_as_ready$",
        MarkEntityReadyView.as_view(),
        name="mark_entity_as_ready",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/mark_as_not_ready$",
        MarkGeneNotReadyView.as_view(),
        name="mark_entity_as_not_ready",
    ),
    # AJAX endpoints
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/delete$",
        DeleteEntityAjaxView.as_view(),
        name="delete_entity",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/approve$",
        ApproveEntityAjaxView.as_view(),
        name="approve_entity",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_sources$",
        ClearSourcesAjaxView.as_view(),
        name="clear_entity_sources",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_source/(?P<source>(.*))/$",
        ClearSingleSourceAjaxView.as_view(),
        name="clear_entity_source",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_phenotypes$",
        ClearPhoenotypesAjaxView.as_view(),
        name="clear_entity_phenotypes",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_transcript$",
        ClearTranscriptAjaxView.as_view(),
        name="clear_entity_transcript",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_publications$",
        ClearPublicationsAjaxView.as_view(),
        name="clear_entity_publications",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_mode_of_pathogenicity$",
        ClearModeOfPathogenicityAjaxView.as_view(),
        name="clear_entity_mode_of_pathogenicity",
    ),
    # AJAX Review endpoints
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_entity_tags/$",
        UpdateEntityTagsAjaxView.as_view(),
        name="update_entity_tags",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_entity_rating/$",
        UpdateEntityRatingAjaxView.as_view(),
        name="update_entity_rating",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_entity_moi/$",
        UpdateEntityMOIAjaxView.as_view(),
        name="update_entity_moi",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_entity_mop/$",
        UpdateEntityMOPAjaxView.as_view(),
        name="update_entity_mop",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_entity_phenotypes/$",
        UpdateEntityPhenotypesAjaxView.as_view(),
        name="update_entity_phenotypes",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_entity_publications/$",
        UpdateEntityPublicationsAjaxView.as_view(),
        name="update_entity_publications",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/delete_evaluation/(?P<evaluation_pk>[0-9]+)/$",
        DeleteEntityEvaluationAjaxView.as_view(),
        name="delete_evaluation_by_user",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/edit_comment/{COMMENT_PK_PARAM}/$",
        GetEntityCommentFormAjaxView.as_view(),
        name="edit_comment_by_user",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/submit_edit_comment/{COMMENT_PK_PARAM}/$",
        SubmitEntityCommentFormAjaxView.as_view(),
        name="submit_edit_comment_by_user",
    ),
    url(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/delete_comment/{COMMENT_PK_PARAM}/$",
        DeleteEntityCommentAjaxView.as_view(),
        name="delete_comment_by_user",
    ),
    url(
        rf"^{PK_PARAM}/mark_not_ready$",
        PanelMarkNotReadyView.as_view(),
        name="mark_not_ready",
    ),
    url(
        r"^(?P<pk>[a-z0-9]{24})/(?P<uri>.*|$)",
        OldCodeURLRedirect.as_view(),
        name="old_code_url_redirect",
    ),
    url(r"^create/", CreatePanelView.as_view(), name="create"),
    url(r"^entities/$", EntitiesListView.as_view(), name="entities_list"),
    url(r"^genes/$", RedirectView.as_view(url="/panels/entities"), name="genes_list"),
    url(rf"^entities/{NAME_PARAM}$", EntityDetailView.as_view(), name="entity_detail",),
    url(rf"^genes/{NAME_PARAM}$", GeneDetailRedirectView.as_view(),),
    url(r"^activity/$", ActivityListView.as_view(), name="activity"),
    url(r"^admin/", AdminView.as_view(), name="admin"),
    url(r"^upload_genes/", AdminUploadGenesView.as_view(), name="upload_genes"),
    url(r"^download_genes/", DownloadAllGenes.as_view(), name="download_genes"),
    url(r"^download_strs/", DownloadAllSTRs.as_view(), name="download_strs"),
    url(r"^download_regions/", DownloadAllRegions.as_view(), name="download_regions"),
    url(r"^upload_panel/", AdminUploadPanelsView.as_view(), name="upload_panels"),
    url(r"^download_panel/", DownloadAllPanels.as_view(), name="download_panels"),
    url(r"^upload_reviews/", AdminUploadReviewsView.as_view(), name="upload_reviews"),
]
