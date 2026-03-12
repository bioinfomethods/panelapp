import json
import logging
import mimetypes
import re

from django.conf import settings
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.views import View

from panelapp.mixins import GELReviewerRequiredMixin
from django.db.models import F, OuterRef, Subquery

from panels.models import Evaluation, Gene, LiteratureAssignment
from s3_storages import ReportsStorage

logger = logging.getLogger(__name__)


class ReportProxyView(GELReviewerRequiredMixin, View):
    """Proxy files from S3 reports bucket with CSRF token and assignment data injection."""

    def get(self, request, path):
        storage = ReportsStorage()

        try:
            with storage.open(path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            raise Http404(f"Report not found: {path}")

        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"

        # Inject CSRF token and assignment data for HTML files
        if content_type == "text/html":
            content = content.decode("utf-8")

            # Inject CSRF token
            csrf_token = get_token(request)
            content = content.replace("{{CSRF_TOKEN}}", csrf_token)

            # Inject static URL for assets
            content = content.replace("{{STATIC_URL}}", settings.STATIC_URL)

            # Parse report config and inject assignment data
            report_config = self._parse_report_config(content)
            if report_config:
                content = self._inject_assignment_data(content, request, report_config)

            content = content.encode("utf-8")

        return HttpResponse(content, content_type=content_type)

    def _parse_report_config(self, html):
        """
        Extract report-config JSON from embedded script tag.
        Returns None if not found (non-assignment-enabled report).
        """
        pattern = r'<script[^>]+id=["\']report-config["\'][^>]*>(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        if not match:
            return None

        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid report-config JSON: {e}")

    def _inject_assignment_data(self, html, request, report_config):
        """Inject assignment data as a JSON block for the JS widget to consume."""
        # Validate required report-config fields (fail-fast)
        if "report_id" not in report_config:
            raise ValueError("report-config missing required 'report_id'")
        if "target_panel_ids" not in report_config:
            raise ValueError("report-config missing required 'target_panel_ids'")
        if "genes" not in report_config:
            raise ValueError("report-config missing required 'genes'")

        report_id = report_config["report_id"]

        # Get curators
        curators = self._get_curators()

        # Get assignments for this report
        assignments = list(
            LiteratureAssignment.objects.filter(report_id=report_id).select_related(
                "gene", "assigned_to", "skipped_by"
            )
        )

        # Match genes against report-config keys (gene_symbol or hgnc_id)
        report_gene_keys = set(report_config["genes"].keys())

        assignments_dict = {}
        gene_pk_to_key = {}
        for a in assignments:
            if a.gene.gene_symbol in report_gene_keys:
                key = a.gene.gene_symbol
            elif a.gene.hgnc_id and a.gene.hgnc_id in report_gene_keys:
                key = a.gene.hgnc_id
            else:
                continue
            gene_pk_to_key[a.gene_id] = key
            assignments_dict[key] = {
                "status": a.status,
                "assigned_to": a.assigned_to_id,
                "assigned_to_display": (
                    a.assigned_to.get_full_name() if a.assigned_to else None
                ),
                "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
                "skipped_by": a.skipped_by_id,
                "skipped_reason": a.skipped_reason,
                "updated_at": a.updated_at.isoformat(),
            }

        # Check completions for assigned genes
        completions = {}
        assigned = [
            a
            for a in assignments
            if a.status == LiteratureAssignment.STATUS.assigned and a.assigned_to_id
        ]

        if assigned:
            completions = self._check_completions(
                assigned, report_config["target_panel_ids"], gene_pk_to_key
            )

        data = {
            "reportId": report_id,
            "currentUserId": request.user.id,
            "curators": curators,
            "assignments": assignments_dict,
            "completions": completions,
        }

        # Inject as JSON block before </body>
        script = f"""
<script type="application/json" id="assignment-data">
{json.dumps(data)}
</script>
</body>"""

        return html.replace("</body>", script)

    def _get_curators(self):
        """Get list of users in Curator group. Raises if group doesn't exist."""
        curator_group = Group.objects.get(name="Curators")  # Let DoesNotExist propagate
        return [
            {
                "id": u.id,
                "username": u.username,
                "display": u.get_full_name() or u.username,
                "initials": (
                    f"{u.first_name[:1]}{u.last_name[:1]}".upper()
                    if u.first_name and u.last_name
                    else u.username[:2].upper()
                ),
            }
            for u in curator_group.user_set.all()
        ]

    def _check_completions(self, assigned, panel_ids, gene_pk_to_key):
        """
        Check completions for assigned genes using a single optimized query.

        Uses Gene FK for all DB queries (version-agnostic), then maps results
        to report-config keys via gene_pk_to_key at the output layer.
        """
        if not assigned:
            return {}

        report_id = assigned[0].report_id
        gene_pks = [a.gene_id for a in assigned if a.gene_id in gene_pk_to_key]

        # Subquery: for each evaluation, find the matching LiteratureAssignment
        # (same report, same gene, user is the assignee) and get assigned_at
        assigned_at_sq = LiteratureAssignment.objects.filter(
            report_id=report_id,
            gene_id=OuterRef("genepanelentrysnapshot__gene_core_id"),
            assigned_to_id=OuterRef("user_id"),
        ).values("assigned_at")[:1]

        # Query evaluations, annotating with assignment date, then filter
        # to only those created after assignment by the assigned user
        evaluations = (
            Evaluation.objects.filter(
                genepanelentrysnapshot__panel__panel__pk__in=panel_ids,
                genepanelentrysnapshot__gene_core_id__in=gene_pks,
            )
            .annotate(
                assignment_date=Subquery(assigned_at_sq),
                gene_pk=F("genepanelentrysnapshot__gene_core_id"),
            )
            .filter(
                assignment_date__isnull=False,  # User is assigned to this gene
                modified__gte=F(
                    "assignment_date"
                ),  # Evaluation updated after assignment
            )
            .values("gene_pk", "rating")
            .distinct()
        )

        # Aggregate ratings per gene, keyed by report-config key
        results = {}
        for ev in evaluations:
            key = gene_pk_to_key.get(ev["gene_pk"])
            if not key:
                continue
            if key not in results:
                results[key] = {"ratings": set()}
            results[key]["ratings"].add(ev["rating"])

        return {
            key: {
                "has_evaluation": True,
                "ratings": list(data["ratings"]),
            }
            for key, data in results.items()
        }


class PrefillFormView(GELReviewerRequiredMixin, View):
    """Store prefill data in session and redirect to target form."""

    def post(self, request):
        form_type = request.POST.get("form_type")

        if form_type == "add":
            return self._handle_add_prefill(request)
        elif form_type == "review":
            return self._handle_review_prefill(request)
        else:
            raise Http404(f"Unknown form type: {form_type}")

    def _resolve_gene_from_post(self, request):
        """Resolve Gene from POST data. Accepts hgnc_id or gene_symbol."""
        hgnc_id = request.POST.get("hgnc_id", "").strip()
        if hgnc_id:
            return Gene.objects.get(hgnc_id=hgnc_id)

        gene_symbol = request.POST.get("gene_symbol", "").strip()
        if gene_symbol:
            return Gene.objects.get(gene_symbol=gene_symbol)

        raise ValueError("Either hgnc_id or gene_symbol is required")

    def _handle_add_prefill(self, request):
        """Handle prefill for adding a new gene."""
        gene = None
        try:
            gene = self._resolve_gene_from_post(request)
        except (Gene.DoesNotExist, ValueError) as e:
            logger.warning(f"Gene resolution failed for prefill: {e}")

        prefill_data = {
            "form_type": "add",
            "gene": gene.pk if gene else None,
            "gene_name": gene.gene_symbol if gene else "",
            "source": request.POST.getlist("source") or ["Literature"],
            "rating": request.POST.get("rating"),
            "moi": request.POST.get("moi"),
            "mode_of_pathogenicity": request.POST.get("mode_of_pathogenicity"),
            "publications": request.POST.get("publications", ""),
            "phenotypes": request.POST.get("phenotypes", ""),
            "comments": request.POST.get("comments", ""),
        }

        request.session["prefill_data"] = prefill_data

        panel_id = request.POST.get("panel_id")
        return redirect("panels:add_entity", pk=panel_id, entity_type="gene")

    def _handle_review_prefill(self, request):
        """Handle prefill for reviewing an existing gene."""
        prefill_data = {
            "form_type": "review",
            "rating": request.POST.get("rating"),
            "moi": request.POST.get("moi"),
            "mode_of_pathogenicity": request.POST.get("mode_of_pathogenicity"),
            "publications": request.POST.get("publications", ""),
            "phenotypes": request.POST.get("phenotypes", ""),
            "current_diagnostic": request.POST.get("current_diagnostic") == "true",
            "comments": request.POST.get("comments", ""),
        }

        request.session["prefill_data"] = prefill_data

        panel_id = request.POST.get("panel_id")
        gene = self._resolve_gene_from_post(request)

        return redirect(
            "panels:review_entity",
            pk=panel_id,
            entity_type="gene",
            entity_name=gene.gene_symbol,
        )
