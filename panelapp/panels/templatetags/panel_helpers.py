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
import re

from django import template
from django.conf import settings
from django.utils.safestring import SafeString

from panels.enums import (
    GeneDataType,
    GeneStatus,
)

register = template.Library()

GENE_LIST_RATING = (
    ("gel-added", "No list", "No list", "grey"),
    ("gel-red", "Red List (low evidence)", "Red", "red"),
    ("gel-amber", "Amber List (moderate evidence)", "Amber", "amber"),
    ("gel-green", "Green List (high evidence)", "Green", "green"),
)


def get_gene_list_data(gene, list_type, saved_gel_status=None, flagged=None):
    if saved_gel_status is not None:
        value = saved_gel_status
    else:
        value = gene.get("saved_gel_status") if isinstance(gene, dict) else gene.status
        if flagged is None:
            flagged = gene.get("flagged") if isinstance(gene, dict) else gene.flagged
    if flagged:
        return GENE_LIST_RATING[GeneStatus.NOLIST.value][list_type]
    elif value > 2:
        return GENE_LIST_RATING[GeneStatus.GREEN.value][list_type]
    elif value == 2:
        return GENE_LIST_RATING[GeneStatus.AMBER.value][list_type]
    elif value == 1:
        return GENE_LIST_RATING[GeneStatus.RED.value][list_type]
    else:
        return GENE_LIST_RATING[GeneStatus.NOLIST.value][list_type]


def get_review_rating_data(review, list_type):
    from panels.models import Evaluation

    if review.rating == Evaluation.RATINGS.GREEN:
        return GENE_LIST_RATING[GeneStatus.GREEN.value][list_type]
    elif review.rating == Evaluation.RATINGS.AMBER:
        return GENE_LIST_RATING[GeneStatus.AMBER.value][list_type]
    elif review.rating == Evaluation.RATINGS.RED:
        return GENE_LIST_RATING[GeneStatus.RED.value][list_type]


@register.filter
def evaluation_rating_name(review):
    from panels.models import Evaluation

    try:
        return Evaluation.RATINGS[review.rating]
    except KeyError:
        return review


@register.filter
def evaluation_rating_class(review):
    return get_review_rating_data(review, GeneDataType.CLASS.value)


@register.filter
def gene_list_class(gene):
    return get_gene_list_data(gene, GeneDataType.CLASS.value)


@register.filter
def gene_list_name(gene):
    return get_gene_list_data(gene, GeneDataType.LONG.value)


@register.filter
def gene_list_short_name(gene):
    return get_gene_list_data(gene, GeneDataType.SHORT.value)


@register.filter
def reviewed_by(gene, user):
    return True if user.is_authenticated and gene.is_reviewd_by_user(user) else False


@register.filter
def human_issue_type(issue_type):
    from panels.models import TrackRecord

    issues = issue_type.split(",")
    out_arr = []

    for issue in issues:
        try:
            out_arr.append(TrackRecord.ISSUE_TYPES[issue])
        except KeyError:
            out_arr.append(issue)

    return ", ".join(out_arr)


@register.filter
def get_ensembleId(transcripts):
    return transcripts.get("GRch38", {}).get("89", {}).get("ensembl_id", None)


@register.filter
def pubmed_link(publication):
    # Pubmed IDs are 1-8 digits, but not all strings of digits are pubmed IDs
    # Assume that 7-8 chars is a pubmed ID and link to it.
    parts = re.split("([0-9]{7,8})", publication)
    for i, part in enumerate(parts):
        if re.search("^[0-9]{7,8}$", part):
            part = SafeString(
                '<a href="http://www.ncbi.nlm.nih.gov/pubmed/'
                + part
                + '">'
                + part
                + "</a>"
            )
            parts[i] = part
    return parts


@register.filter
def remove_special(seq):
    return re.sub("\W+", "", seq)


@register.filter
def human_variant_types(variant_type):
    from panels.models import Region

    return Region.VARIANT_TYPES[variant_type]


@register.simple_tag
def signed_off_panel_message(panel: "panels.models.GenePanelSnapshot") -> str:
    if not settings.SIGNED_OFF_MESSAGE:
        return ""

    version = f"{panel.major_version}.{panel.minor_version}"
    return settings.SIGNED_OFF_MESSAGE.format(version=version)
