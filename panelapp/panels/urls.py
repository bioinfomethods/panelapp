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
from django.urls import re_path
from django.views.generic import RedirectView

from panels.views.feedback import (
    clear_entity_mode_of_pathogenicity_view,
    clear_entity_phenotypes_view,
    clear_entity_publications_view,
    clear_entity_source_for_entity_list_view,
    clear_entity_source_view,
    clear_entity_sources_view,
    clear_entity_transcript_view,
    delete_entity_comment_view,
    delete_evaluation_by_user_view,
    edit_entity_comment_form_view,
    panel_entity_detail_view,
    toggle_entity_ready_view,
    update_entity_moi_view,
    update_entity_mop_view,
    update_entity_phenotypes_view,
    update_entity_publications_view,
    update_entity_rating_view,
    update_entity_tags_view,
)

from .ajax_views import (
    ApproveEntityAjaxView,
    ApprovePanelAjaxView,
    DeleteEntityAjaxView,
    DeletePanelAjaxView,
    RejectPanelAjaxView,
    SubmitEntityCommentFormAjaxView,
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
    GenePanelView,
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
    re_path(r"^$", PanelsIndexView.as_view(), name="index"),
    re_path(r"^compare/$", ComparePanelsView.as_view(), name="compare_panels_form"),
    re_path(
        r"^compare/(?P<panel_1_id>[0-9]+)/(?P<panel_2_id>[0-9]+)$",
        ComparePanelsView.as_view(),
        name="compare",
    ),
    re_path(
        r"^compare/(?P<panel_1_id>[0-9]+)/(?P<panel_2_id>[0-9]+)/(?P<gene_symbol>[\w\-]+)$",
        CompareGeneView.as_view(),
        name="compare_genes",
    ),
    re_path(
        r"^copy/(?P<panel_1_id>[0-9]+)/(?P<panel_2_id>[0-9]+)$",
        CopyReviewsView.as_view(),
        name="copy_reviews",
    ),
    re_path(rf"^{PK_PARAM}/$", GenePanelView.as_view(), name="detail"),
    re_path(rf"^{PK_PARAM}/update$", UpdatePanelView.as_view(), name="update"),
    re_path(rf"^{PK_PARAM}/promote$", PromotePanelView.as_view(), name="promote"),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/add$",
        PanelAddEntityView.as_view(),
        name="add_entity",
    ),
    re_path(
        rf"^{PK_PARAM}/delete$", DeletePanelAjaxView.as_view(), name="delete_panel"
    ),
    re_path(
        rf"^{PK_PARAM}/reject$", RejectPanelAjaxView.as_view(), name="reject_panel"
    ),
    re_path(
        rf"^{PK_PARAM}/approve$",
        ApprovePanelAjaxView.as_view(),
        name="approve_panel",
    ),
    re_path(
        rf"^{PK_PARAM}/download/(?P<categories>[0-4]+)/$",
        DownloadPanelTSVView.as_view(),
        name="download_panel_tsv",
    ),
    re_path(
        rf"^{PK_PARAM}/download_version/$",
        DownloadPanelVersionTSVView.as_view(),
        name="download_old_panel_tsv",
    ),
    re_path(
        rf"^{PK_PARAM}/{NAME_PARAM}/$",
        RedirectGenesToEntities.as_view(),
        name="redirect_previous_structure",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/$",
        panel_entity_detail_view,
        name="evaluation",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/edit$",
        PanelEditEntityView.as_view(),
        name="edit_entity",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/review$",
        EntityReviewView.as_view(),
        name="review_entity",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/mark_entity_as_ready$",
        toggle_entity_ready_view,
        name="mark_entity_as_ready",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/mark_entity_as_not_ready$",
        toggle_entity_ready_view,
        name="mark_entity_as_not_ready",
    ),
    # AJAX endpoints
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/delete$",
        DeleteEntityAjaxView.as_view(),
        name="delete_entity",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/approve$",
        ApproveEntityAjaxView.as_view(),
        name="approve_entity",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_sources$",
        clear_entity_sources_view,
        name="clear_entity_sources",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_source/(?P<source>(.*))/$",
        clear_entity_source_view,
        name="clear_entity_source",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_source_for_entity_list/(?P<source>(.*))/$",
        clear_entity_source_for_entity_list_view,
        name="clear_entity_source_for_entity_list",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_phenotypes$",
        clear_entity_phenotypes_view,
        name="clear_entity_phenotypes",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_transcript$",
        clear_entity_transcript_view,
        name="clear_entity_transcript",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_publications$",
        clear_entity_publications_view,
        name="clear_entity_publications",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/clear_entity_mode_of_pathogenicity$",
        clear_entity_mode_of_pathogenicity_view,
        name="clear_entity_mode_of_pathogenicity",
    ),
    # AJAX Review endpoints
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_tags/$",
        update_entity_tags_view,
        name="update_entity_tags",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_rating/$",
        update_entity_rating_view,
        name="update_entity_rating",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_moi/$",
        update_entity_moi_view,
        name="update_entity_moi",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_mop/$",
        update_entity_mop_view,
        name="update_entity_mop",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_phenotypes/$",
        update_entity_phenotypes_view,
        name="update_entity_phenotypes",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/update_publications/$",
        update_entity_publications_view,
        name="update_entity_publications",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/delete_evaluation/(?P<evaluation_pk>[0-9]+)/$",
        delete_evaluation_by_user_view,
        name="delete_evaluation_by_user",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/edit_comment/{COMMENT_PK_PARAM}/$",
        edit_entity_comment_form_view,
        name="edit_comment_by_user",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/submit_edit_comment/{COMMENT_PK_PARAM}/$",
        SubmitEntityCommentFormAjaxView.as_view(),
        name="submit_edit_comment_by_user",
    ),
    re_path(
        rf"^{PK_PARAM}/{TYPE_PARAM}/{NAME_PARAM}/delete_comment/{COMMENT_PK_PARAM}/$",
        delete_entity_comment_view,
        name="delete_comment_by_user",
    ),
    re_path(
        rf"^{PK_PARAM}/mark_not_ready$",
        PanelMarkNotReadyView.as_view(),
        name="mark_not_ready",
    ),
    re_path(
        r"^(?P<pk>[a-z0-9]{24})/(?P<uri>.*|$)",
        OldCodeURLRedirect.as_view(),
        name="old_code_url_redirect",
    ),
    re_path(r"^create/", CreatePanelView.as_view(), name="create"),
    re_path(r"^entities/$", EntitiesListView.as_view(), name="entities_list"),
    re_path(
        r"^genes/$", RedirectView.as_view(url="/panels/entities"), name="genes_list"
    ),
    re_path(
        rf"^entities/{NAME_PARAM}$",
        EntityDetailView.as_view(),
        name="entity_detail",
    ),
    re_path(
        rf"^genes/{NAME_PARAM}$",
        GeneDetailRedirectView.as_view(),
    ),
    re_path(r"^activity/$", ActivityListView.as_view(), name="activity"),
    re_path(r"^admin/", AdminView.as_view(), name="admin"),
    re_path(r"^upload_genes/", AdminUploadGenesView.as_view(), name="upload_genes"),
    re_path(r"^download_genes/", DownloadAllGenes.as_view(), name="download_genes"),
    re_path(r"^download_strs/", DownloadAllSTRs.as_view(), name="download_strs"),
    re_path(
        r"^download_regions/", DownloadAllRegions.as_view(), name="download_regions"
    ),
    re_path(r"^upload_panel/", AdminUploadPanelsView.as_view(), name="upload_panels"),
    re_path(r"^download_panel/", DownloadAllPanels.as_view(), name="download_panels"),
    re_path(
        r"^upload_reviews/", AdminUploadReviewsView.as_view(), name="upload_reviews"
    ),
]
