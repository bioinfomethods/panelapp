#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "tqdm",
# ]
# ///
"""
Fetch gene data from HGNC and Ensembl to generate a PanelApp genes.json fixture.

This script downloads:
1. HGNC complete gene set (symbols, aliases, OMIM IDs, etc.)
2. Ensembl GTF for GRCh38 (coordinates, biotype)
3. Ensembl GTF for GRCh37 (coordinates)

And joins them to produce a genes.json fixture file compatible with PanelApp.

Usage:
    uv run --script scripts/fetch_genes.py [--output FILE]

Example:
    uv run --script scripts/fetch_genes.py -o genes.json
    uv run --script scripts/fetch_genes.py -o genes.json.gz  # gzip output
"""

import argparse
import gzip
import json
import re
import sys
from dataclasses import dataclass, field
import httpx
from tqdm import tqdm

# Data source URLs
HGNC_URL = "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt"

# Ensembl release versions
ENSEMBL_GRCH38_RELEASE = 115
ENSEMBL_GRCH37_RELEASE = 87  # Last release with GRCh37 updates

ENSEMBL_GRCH38_GTF_URL = f"https://ftp.ensembl.org/pub/release-{ENSEMBL_GRCH38_RELEASE}/gtf/homo_sapiens/Homo_sapiens.GRCh38.{ENSEMBL_GRCH38_RELEASE}.gtf.gz"
ENSEMBL_GRCH37_GTF_URL = f"https://ftp.ensembl.org/pub/grch37/release-{ENSEMBL_GRCH37_RELEASE}/gtf/homo_sapiens/Homo_sapiens.GRCh37.{ENSEMBL_GRCH37_RELEASE}.gtf.gz"


@dataclass
class HGNCGene:
    hgnc_id: str
    symbol: str
    name: str
    alias_symbol: list[str] = field(default_factory=list)
    alias_name: list[str] = field(default_factory=list)
    prev_symbol: list[str] = field(default_factory=list)
    date_symbol_changed: str | None = None
    date_modified: str | None = None
    ensembl_gene_id: str | None = None
    omim_id: list[str] = field(default_factory=list)
    locus_type: str | None = None


@dataclass
class EnsemblGene:
    gene_id: str
    chromosome: str
    start: int
    end: int
    biotype: str
    gene_name: str | None = None


def parse_hgnc_tsv(content: str) -> dict[str, HGNCGene]:
    """Parse HGNC TSV file and return dict keyed by Ensembl gene ID."""
    lines = content.strip().split("\n")
    header = lines[0].split("\t")

    # Find column indices
    cols = {name: idx for idx, name in enumerate(header)}

    genes_by_ensembl = {}
    genes_by_symbol = {}

    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) < len(header):
            fields.extend([""] * (len(header) - len(fields)))

        # Skip non-approved genes
        status = fields[cols.get("status", 0)]
        if status != "Approved":
            continue

        def get_field(name: str) -> str:
            idx = cols.get(name)
            if idx is None or idx >= len(fields):
                return ""
            return fields[idx].strip()

        def get_list_field(name: str) -> list[str]:
            val = get_field(name)
            if not val:
                return []
            # HGNC wraps multi-value fields in quotes and uses | as separator
            val = val.strip('"')
            return [x.strip() for x in val.split("|") if x.strip()]

        gene = HGNCGene(
            hgnc_id=get_field("hgnc_id"),
            symbol=get_field("symbol"),
            name=get_field("name"),
            alias_symbol=get_list_field("alias_symbol"),
            alias_name=get_list_field("alias_name"),
            prev_symbol=get_list_field("prev_symbol"),
            date_symbol_changed=get_field("date_symbol_changed") or None,
            date_modified=get_field("date_modified") or None,
            ensembl_gene_id=get_field("ensembl_gene_id") or None,
            omim_id=get_list_field("omim_id"),
            locus_type=get_field("locus_type") or None,
        )

        genes_by_symbol[gene.symbol] = gene
        if gene.ensembl_gene_id:
            genes_by_ensembl[gene.ensembl_gene_id] = gene

    return genes_by_ensembl, genes_by_symbol


def parse_gtf_genes(content: bytes) -> dict[str, EnsemblGene]:
    """Parse Ensembl GTF and extract gene records."""
    genes = {}

    # Decompress if gzipped
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)

    for line in content.decode("utf-8").split("\n"):
        if line.startswith("#") or not line.strip():
            continue

        fields = line.split("\t")
        if len(fields) < 9:
            continue

        # Only process gene features
        if fields[2] != "gene":
            continue

        chrom = fields[0]
        start = int(fields[3])
        end = int(fields[4])
        attributes = fields[8]

        # Parse GTF attributes
        attr_dict = {}
        for attr in attributes.split(";"):
            attr = attr.strip()
            if not attr:
                continue
            match = re.match(r'(\w+)\s+"([^"]*)"', attr)
            if match:
                attr_dict[match.group(1)] = match.group(2)

        gene_id = attr_dict.get("gene_id")
        if not gene_id:
            continue

        # Remove version suffix from gene_id (e.g., ENSG00000121410.12 -> ENSG00000121410)
        gene_id_base = gene_id.split(".")[0]

        genes[gene_id_base] = EnsemblGene(
            gene_id=gene_id_base,
            chromosome=chrom,
            start=start,
            end=end,
            biotype=attr_dict.get("gene_biotype", ""),
            gene_name=attr_dict.get("gene_name"),
        )

    return genes


def convert_to_panelapp_format(
    hgnc_gene: HGNCGene,
    ensembl_grch38: EnsemblGene | None,
    ensembl_grch37: EnsemblGene | None,
) -> dict:
    """Convert gene data to PanelApp fixture format."""
    ensembl_genes = {}

    if ensembl_grch38:
        ensembl_genes["GRch38"] = {
            str(ENSEMBL_GRCH38_RELEASE): {
                "ensembl_id": ensembl_grch38.gene_id,
                "location": f"{ensembl_grch38.chromosome}:{ensembl_grch38.start}-{ensembl_grch38.end}",
            }
        }

    if ensembl_grch37:
        ensembl_genes["GRch37"] = {
            str(ENSEMBL_GRCH37_RELEASE): {
                "ensembl_id": ensembl_grch37.gene_id,
                "location": f"{ensembl_grch37.chromosome}:{ensembl_grch37.start}-{ensembl_grch37.end}",
            }
        }

    # Determine biotype (prefer GRCh38)
    biotype = None
    if ensembl_grch38:
        biotype = ensembl_grch38.biotype
    elif ensembl_grch37:
        biotype = ensembl_grch37.biotype

    # Format OMIM IDs as JSON string array (matching existing format)
    omim_gene = None
    if hgnc_gene.omim_id:
        omim_gene = json.dumps(hgnc_gene.omim_id)

    # Format aliases as JSON string array (use "[]" for empty, not null)
    all_aliases = hgnc_gene.alias_symbol + hgnc_gene.prev_symbol
    alias = json.dumps(all_aliases) if all_aliases else "[]"

    # Format alias names as JSON string array
    alias_name = None
    if hgnc_gene.alias_name:
        alias_name = json.dumps(hgnc_gene.alias_name)

    # Determine if gene is active (has Ensembl data)
    active = bool(ensembl_genes)

    return {
        "model": "panels.gene",
        "pk": hgnc_gene.symbol,
        "fields": {
            "gene_name": hgnc_gene.name,
            "ensembl_genes": ensembl_genes,
            "omim_gene": omim_gene,
            "alias": alias,
            "biotype": biotype,
            "alias_name": alias_name,
            "hgnc_symbol": hgnc_gene.symbol,
            "hgnc_date_symbol_changed": hgnc_gene.date_symbol_changed,
            "hgnc_release": hgnc_gene.date_modified,
            "hgnc_id": hgnc_gene.hgnc_id,
            "active": active,
        },
    }


def download_file(client: httpx.Client, url: str, description: str) -> bytes:
    """Download a file with progress bar."""
    with client.stream("GET", url, follow_redirects=True) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        chunks = []

        with tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            desc=description,
            file=sys.stderr,
        ) as pbar:
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                pbar.update(len(chunk))

    return b"".join(chunks)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch gene data from HGNC and Ensembl"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=None,
        help="JSON indentation (default: compact)",
    )
    args = parser.parse_args()

    client = httpx.Client(
        headers={"User-Agent": "PanelApp-Gene-Fetcher/1.0"},
        timeout=300,
    )

    # Download HGNC data
    hgnc_content = download_file(client, HGNC_URL, "HGNC")
    print("Parsing HGNC data...", file=sys.stderr)
    hgnc_by_ensembl, hgnc_by_symbol = parse_hgnc_tsv(hgnc_content.decode("utf-8"))
    print(f"  Found {len(hgnc_by_symbol)} approved genes", file=sys.stderr)

    # Download Ensembl GRCh38 GTF
    grch38_content = download_file(
        client, ENSEMBL_GRCH38_GTF_URL, f"GRCh38.{ENSEMBL_GRCH38_RELEASE}"
    )
    print("Parsing GRCh38 GTF...", file=sys.stderr)
    ensembl_grch38 = parse_gtf_genes(grch38_content)
    print(f"  Found {len(ensembl_grch38)} genes", file=sys.stderr)

    # Download Ensembl GRCh37 GTF
    grch37_content = download_file(
        client, ENSEMBL_GRCH37_GTF_URL, f"GRCh37.{ENSEMBL_GRCH37_RELEASE}"
    )
    print("Parsing GRCh37 GTF...", file=sys.stderr)
    ensembl_grch37 = parse_gtf_genes(grch37_content)
    print(f"  Found {len(ensembl_grch37)} genes", file=sys.stderr)

    # Join and convert
    print("Joining data...", file=sys.stderr)
    genes = []
    matched_grch38 = 0
    matched_grch37 = 0

    for symbol, hgnc_gene in sorted(hgnc_by_symbol.items()):
        ens_id = hgnc_gene.ensembl_gene_id

        grch38_gene = ensembl_grch38.get(ens_id) if ens_id else None
        grch37_gene = ensembl_grch37.get(ens_id) if ens_id else None

        if grch38_gene:
            matched_grch38 += 1
        if grch37_gene:
            matched_grch37 += 1

        genes.append(convert_to_panelapp_format(hgnc_gene, grch38_gene, grch37_gene))

    print(f"  Matched {matched_grch38} genes to GRCh38", file=sys.stderr)
    print(f"  Matched {matched_grch37} genes to GRCh37", file=sys.stderr)
    print(f"  Total genes: {len(genes)}", file=sys.stderr)

    # Output
    output = json.dumps(genes, indent=args.indent)
    if args.output:
        if args.output.endswith(".gz"):
            with gzip.open(args.output, "wt", encoding="utf-8") as f:
                f.write(output)
        else:
            with open(args.output, "w") as f:
                f.write(output)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
