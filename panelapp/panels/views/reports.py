import logging
import mimetypes

from django.http import Http404
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.views import View

from panelapp.mixins import GELReviewerRequiredMixin
from panels.models import Gene
from s3_storages import ReportsStorage

logger = logging.getLogger(__name__)


class ReportProxyView(GELReviewerRequiredMixin, View):
    """Proxy files from S3 reports bucket with CSRF token injection for HTML."""

    def get(self, request, path):
        storage = ReportsStorage()

        try:
            with storage.open(path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            raise Http404(f"Report not found: {path}")

        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"

        # Inject CSRF token for HTML files
        if content_type == "text/html":
            content = content.decode("utf-8")
            csrf_token = get_token(request)
            content = content.replace("{{CSRF_TOKEN}}", csrf_token)
            content = content.encode("utf-8")

        return HttpResponse(content, content_type=content_type)


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

    def _handle_add_prefill(self, request):
        """Handle prefill for adding a new gene."""
        gene_symbol = request.POST.get("gene_symbol", "").strip()

        # Look up gene by symbol to get PK
        gene_pk = None
        if gene_symbol:
            try:
                gene = Gene.objects.get(gene_symbol=gene_symbol)
                gene_pk = gene.pk
            except Gene.DoesNotExist:
                logger.warning(f"Gene not found for symbol: {gene_symbol}")

        prefill_data = {
            "form_type": "add",
            "gene": gene_pk,
            "gene_name": request.POST.get("gene_name", gene_symbol),
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
        gene_name = request.POST.get("gene_name")
        return redirect(
            "panels:review_entity",
            pk=panel_id,
            entity_type="gene",
            entity_name=gene_name,
        )
