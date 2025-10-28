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
from rest_framework import serializers
from panels.models import GenePanelSnapshot
from panels.models import GenePanelEntrySnapshot
from panels.models import STR
from panels.models import Region
from panels.models import Activity
from panels.models import Evaluation
from panels.models import PanelType
from panels.models import HistoricalSnapshot
from panels.models import Gene
from panels.models import Evidence
from panels.models import Tag


class NonEmptyItemsListField(serializers.ListField):
    def to_representation(self, data):
        return [self.child.to_representation(item).strip() for item in data if item]


class StatsJSONField(serializers.JSONField):
    def to_representation(self, value):
        whitelist_stats = ["number_of_genes", "number_of_strs", "number_of_regions"]
        out = {}
        for val in whitelist_stats:
            if val in value:
                out[val] = value[val]
        return out


class RangeIntegerField(serializers.ListField):
    def to_representation(self, value):
        return [value.lower, value.upper] if value else None

    def to_internal_value(self, data):
        raise NotImplementedError("Implement it when we add adding genes")


class EvidenceListField(serializers.ListField):
    def to_representation(self, data):
        if data:
            return [e.name for e in data.all()]
        return []


class PanelTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PanelType
        fields = ("name", "slug", "description")


class PanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenePanelSnapshot
        fields = (
            "id",
            "hash_id",
            "name",
            "disease_group",
            "disease_sub_group",
            "description",
            "status",
            "version",
            "version_created",
            "relevant_disorders",
            "stats",
            "types",
        )
        depth = 1

    id = serializers.IntegerField(source="panel_id")
    hash_id = serializers.StringRelatedField(source="panel.old_pk")
    name = serializers.StringRelatedField(source="level4title.name")
    disease_group = serializers.StringRelatedField(source="level4title.level2title")
    disease_sub_group = serializers.StringRelatedField(source="level4title.level3title")
    description = serializers.CharField(source="level4title.description", read_only=True)
    status = serializers.StringRelatedField(source="panel.status")
    version = serializers.CharField(read_only=True)
    version_created = serializers.DateTimeField(source="created", read_only=True)
    relevant_disorders = NonEmptyItemsListField(source="old_panels")
    stats = StatsJSONField(
        help_text="Object with panel statistics (number of genes or STRs)",
        read_only=True,
    )
    types = PanelTypeSerializer(source="panel.types", read_only=True, many=True)

    def __init__(self, *args, **kwargs):
        self.include_entities = False
        if kwargs.get("include_entities", False):
            kwargs.pop("include_entities")
            self.include_entities = True

        super().__init__(*args, **kwargs)

        no_panel = True

        if self.instance and isinstance(self.instance, GenePanelSnapshot):
            if self.instance.is_super_panel:
                no_panel = False

        if self.include_entities:
            self.fields["genes"] = GeneSerializer(
                source="get_all_genes_prefetch",
                many=True,
                read_only=True,
                no_panel=no_panel,
            )
            self.fields["strs"] = STRSerializer(
                source="get_all_strs_prefetch",
                many=True,
                read_only=True,
                no_panel=no_panel,
            )
            self.fields["regions"] = RegionSerializer(
                source="get_all_regions_prefetch",
                many=True,
                read_only=True,
                no_panel=no_panel,
            )


class GeneData(serializers.JSONField):
    alias_name = serializers.CharField(allow_null=True, allow_blank=True)
    ensembl_genes = serializers.DictField()
    hgnc_date_symbol_changed = serializers.DateField()
    hgnc_symbol = serializers.CharField()
    alias = serializers.ListField(
        child=serializers.CharField(allow_blank=False, allow_null=False)
    )
    hgnc_release = serializers.DateTimeField()
    biotype = serializers.CharField()
    gene_symbol = serializers.CharField()
    hgnc_id = serializers.CharField()
    gene_name = serializers.CharField()
    omim_gene = serializers.ListField(
        child=serializers.CharField(allow_null=False, allow_blank=False)
    )


class GeneSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenePanelEntrySnapshot
        fields = (
            "gene_data",
            "entity_type",
            "entity_name",
            "confidence_level",
            "penetrance",
            "mode_of_pathogenicity",
            "publications",
            "evidence",
            "phenotypes",
            "mode_of_inheritance",
            "tags",
            "panel",
            "transcript"
        )

    entity_type = serializers.CharField()
    entity_name = serializers.CharField()
    gene_data = GeneData(source="gene", read_only=True)
    confidence_level = serializers.CharField(
        source="saved_gel_status"
    )  # FIXME(Oleg) use old values or enum...
    mode_of_inheritance = serializers.CharField(source="moi")
    publications = NonEmptyItemsListField()
    phenotypes = NonEmptyItemsListField()
    evidence = EvidenceListField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    panel = PanelSerializer(many=False, read_only=True, required=False, allow_null=True)
    transcript = NonEmptyItemsListField()

    def __init__(self, *args, **kwargs):
        self.no_panel = False
        if kwargs.get("no_panel", False):
            self.no_panel = True
        if "no_panel" in kwargs:
            kwargs.pop("no_panel")
        super().__init__(*args, **kwargs)
        if self.no_panel:
            del self.fields["panel"]

    def get_field_names(self, declared_fields, info):
        field_names = super().get_field_names(declared_fields, info)
        if self.no_panel:
            return [n for n in field_names if field_names != "panel"]
        return field_names


class STRSerializer(GeneSerializer):
    class Meta:
        model = STR
        fields = (
            "gene_data",
            "entity_type",
            "entity_name",
            "confidence_level",
            "penetrance",
            "publications",
            "evidence",
            "phenotypes",
            "mode_of_inheritance",
            "repeated_sequence",
            "chromosome",
            "grch37_coordinates",
            "grch38_coordinates",
            "normal_repeats",
            "pathogenic_repeats",
            "tags",
            "panel",
        )

    grch37_coordinates = RangeIntegerField(
        child=serializers.IntegerField(allow_null=False),
        source="position_37",
        min_length=2,
        max_length=2,
    )
    grch38_coordinates = RangeIntegerField(
        child=serializers.IntegerField(allow_null=False),
        source="position_38",
        min_length=2,
        max_length=2,
    )


class RegionSerializer(GeneSerializer):
    class Meta:
        model = Region
        fields = (
            "gene_data",
            "entity_type",
            "entity_name",
            "verbose_name",
            "confidence_level",
            "penetrance",
            "mode_of_pathogenicity",
            "haploinsufficiency_score",
            "triplosensitivity_score",
            "required_overlap_percentage",
            "type_of_variants",
            "publications",
            "evidence",
            "phenotypes",
            "mode_of_inheritance",
            "chromosome",
            "grch37_coordinates",
            "grch38_coordinates",
            "tags",
            "panel",
        )

    grch37_coordinates = RangeIntegerField(
        child=serializers.IntegerField(allow_null=False),
        source="position_37",
        min_length=2,
        max_length=2,
    )
    grch38_coordinates = RangeIntegerField(
        child=serializers.IntegerField(allow_null=False),
        source="position_38",
        min_length=2,
        max_length=2,
    )


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = (
            "created",
            "panel_name",
            "panel_id",
            "panel_version",
            "user_name",
            "item_type",
            "text",
            "entity_name",
            "entity_type",
        )


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = (
            "created",
            "rating",
            "mode_of_pathogenicity",
            "publications",
            "phenotypes",
            "moi",
            "current_diagnostic",
            "clinically_relevant",
        )


class EntitiesListSerializer(serializers.ListSerializer):
    gene_serializer = None
    str_serializer = None
    region_serializer = None

    def __init__(self, *args, **kwargs):
        self.gene_serializer = GeneSerializer()
        self.str_serializer = STRSerializer()
        self.region_serializer = RegionSerializer()
        super().__init__(*args, **kwargs)

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """

        types_to_serializers = {
            "gene": self.gene_serializer,
            "str": self.str_serializer,
            "region": self.region_serializer,
        }

        return [
            types_to_serializers[item.entity_type].to_representation(item)
            for item in data
        ]


class EntitySerializer(serializers.BaseSerializer):
    class Meta:
        list_serializer_class = EntitiesListSerializer


class HistoricalSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalSnapshot
        fields = (
            "data",
            "signed_off_date",
        )

    def to_representation(self, instance):
        instance.data.pop('genes', None)
        instance.data.pop('regions', None)
        instance.data.pop('strs', None)
        instance.data['signed_off'] = instance.signed_off_date
        return instance.data


class GeneAddSerializer(serializers.Serializer):
    """
    Serializer for adding a gene to a panel (minimal, no review).

    This creates a GenePanelEntrySnapshot with metadata but does NOT
    create an Evaluation record.
    """

    # Required fields
    gene_symbol = serializers.CharField(
        required=True,
        help_text="Gene symbol (e.g., 'BRCA1')"
    )
    sources = serializers.ListField(
        child=serializers.ChoiceField(choices=Evidence.DROPDOWN_SOURCES),
        min_length=1,
        required=True,
        help_text="At least one source required"
    )
    moi = serializers.ChoiceField(
        choices=Evaluation.MODES_OF_INHERITANCE,
        required=True,
        help_text="Mode of inheritance"
    )

    # Optional metadata fields
    mode_of_pathogenicity = serializers.ChoiceField(
        choices=Evaluation.MODES_OF_PATHOGENICITY,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    penetrance = serializers.ChoiceField(
        choices=GenePanelEntrySnapshot.PENETRANCE,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    publications = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of PMIDs"
    )
    phenotypes = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    transcript = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Transcript IDs (GEL users only)"
    )
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Tag IDs (GEL users only)"
    )

    def validate_gene_symbol(self, value):
        """Check if gene exists in reference database and is active"""
        try:
            gene = Gene.objects.get(gene_symbol=value)
            if not gene.active:
                raise serializers.ValidationError(
                    f"Gene '{value}' is not active in the reference database"
                )
        except Gene.DoesNotExist:
            raise serializers.ValidationError(
                f"Gene '{value}' not found in reference database"
            )
        return value

    def validate_tags(self, value):
        """Validate tags: GEL only, IDs must exist"""
        if value:
            request = self.context.get('request')
            if not (request and request.user.is_authenticated and request.user.reviewer.is_GEL()):
                raise serializers.ValidationError(
                    "Only GEL users can assign tags"
                )
            # Validate tag IDs exist
            existing_ids = set(Tag.objects.filter(pk__in=value).values_list('pk', flat=True))
            provided_ids = set(value)
            if existing_ids != provided_ids:
                invalid_ids = provided_ids - existing_ids
                raise serializers.ValidationError(
                    f"Invalid tag IDs: {', '.join(map(str, invalid_ids))}"
                )
        return value

    def validate_transcript(self, value):
        """Only GEL users can add transcript info"""
        if value:
            request = self.context.get('request')
            if not (request and request.user.is_authenticated and request.user.reviewer.is_GEL()):
                raise serializers.ValidationError(
                    "Only GEL users can add transcript information"
                )
        return value

    def validate(self, data):
        """Check if gene already exists in panel"""
        panel = self.context.get('panel')
        gene_symbol = data['gene_symbol']

        if not panel:
            raise serializers.ValidationError("Panel context is required")

        if panel.has_gene(gene_symbol):
            raise serializers.ValidationError({
                'gene_symbol': f"Gene '{gene_symbol}' already exists in this panel"
            })

        return data


class GeneReviewSerializer(serializers.Serializer):
    """
    Serializer for submitting a review/evaluation for a gene in a panel.

    This creates an Evaluation record linked to an existing GenePanelEntrySnapshot.
    Does NOT modify the gene entry's metadata.
    """

    # All fields optional, but at least one should be provided
    rating = serializers.ChoiceField(
        choices=Evaluation.RATINGS,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="GREEN, AMBER, or RED"
    )
    comments = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Review comments"
    )
    moi = serializers.ChoiceField(
        choices=Evaluation.MODES_OF_INHERITANCE,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Reviewer's opinion on mode of inheritance"
    )
    mode_of_pathogenicity = serializers.ChoiceField(
        choices=Evaluation.MODES_OF_PATHOGENICITY,
        required=False,
        allow_null=True,
        allow_blank=True
    )
    publications = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Supporting PMIDs for this review"
    )
    phenotypes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Associated phenotypes for this review"
    )
    current_diagnostic = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Whether this is currently used diagnostically"
    )
    clinically_relevant = serializers.BooleanField(
        required=False,
        default=False,
        help_text="For STRs: whether interruptions are clinically relevant"
    )

    def validate(self, data):
        """Require at least one field to have a meaningful value"""
        # Check if any field has a meaningful value
        has_data = any([
            data.get('rating'),
            data.get('comments'),
            data.get('moi'),
            data.get('mode_of_pathogenicity'),
            data.get('publications'),
            data.get('phenotypes'),
            data.get('current_diagnostic'),
            data.get('clinically_relevant'),
        ])

        if not has_data:
            raise serializers.ValidationError(
                "At least one review field must be provided"
            )

        return data
