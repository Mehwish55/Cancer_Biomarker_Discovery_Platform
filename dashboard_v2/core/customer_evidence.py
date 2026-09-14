from __future__ import annotations

from typing import Any

import pandas as pd


def _clean_value(value):
    """Convert pandas/numpy values into simple Python values."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def _find_gene_row(
    dataframe: pd.DataFrame | None,
    gene_name: str,
):
    """Return the first matching gene row."""
    if dataframe is None or dataframe.empty:
        return None

    if "gene_name" not in dataframe.columns:
        return None

    matches = dataframe[
        dataframe["gene_name"].astype(str).str.upper()
        == str(gene_name).upper()
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def _extract_columns(
    row,
    columns: list[str],
) -> dict[str, Any]:
    """Extract available columns from one row."""
    if row is None:
        return {}

    result = {}

    for column in columns:
        if column in row.index:
            result[column] = _clean_value(row[column])

    return result


def get_customer_biomarker_evidence(
    gene_name: str,
    differential_expression: pd.DataFrame | None = None,
    roc_results: pd.DataFrame | None = None,
    ml_results: dict[str, Any] | None = None,
    stability_results: dict[str, Any] | None = None,
    pathway_results: dict[str, Any] | None = None,
    integrated_ranking: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """
    Collect all available evidence for one customer biomarker.

    This function only retrieves evidence already calculated by the
    customer analysis pipeline. It does not create a new biological score.
    """

    ml_table = None
    if isinstance(ml_results, dict):
        ml_table = ml_results.get("rf_importance")

    stability_table = None
    if isinstance(stability_results, dict):
        stability_table = stability_results.get("stability")

    ranking_row = _find_gene_row(
        integrated_ranking,
        gene_name,
    )

    de_row = _find_gene_row(
        differential_expression,
        gene_name,
    )

    roc_row = _find_gene_row(
        roc_results,
        gene_name,
    )

    ml_row = _find_gene_row(
        ml_table,
        gene_name,
    )

    stability_row = _find_gene_row(
        stability_table,
        gene_name,
    )

    pathway_evidence = []

    if isinstance(pathway_results, dict):
        for ontology in ("BP", "CC", "MF"):
            table = pathway_results.get(ontology)

            if table is None or table.empty:
                continue

            if "contributing_genes" not in table.columns:
                continue

            for _, row in table.iterrows():
                genes = str(
                    row.get("contributing_genes", "")
                )

                gene_tokens = {
                    token.strip().upper()
                    for token in genes.split(",")
                    if token.strip()
                }

                if str(gene_name).upper() not in gene_tokens:
                    continue

                pathway_evidence.append(
                    {
                        "ontology": ontology,
                        "GOID": _clean_value(
                            row.get("GOID")
                        ),
                        "TERM": _clean_value(
                            row.get("TERM")
                        ),
                        "Hits": _clean_value(
                            row.get("Hits")
                        ),
                        "FoldEnrichment": _clean_value(
                            row.get("FoldEnrichment")
                        ),
                        "pvalue": _clean_value(
                            row.get("pvalue")
                        ),
                        "padj": _clean_value(
                            row.get("padj")
                        ),
                    }
                )

    evidence = {
        "gene_name": gene_name,

        "integrated_ranking": _extract_columns(
            ranking_row,
            [
                "integrated_rank",
                "integrated_score",
                "score_DE",
                "score_ROC",
                "score_AUC",
                "score_sensitivity",
                "score_specificity",
                "score_ML",
                "score_stability",
                "score_pathway",
                "AUC",
                "sensitivity",
                "specificity",
                "importance",
                "ML_rank",
            ],
        ),

        "differential_expression": _extract_columns(
            de_row,
            [
                "gene_name",
                "baseMean",
                "log2FoldChange",
                "pvalue",
                "padj",
                "direction",
            ],
        ),

        "roc_validation": _extract_columns(
            roc_row,
            [
                "gene_name",
                "AUC",
                "sensitivity",
                "specificity",
                "threshold",
                "direction",
                "reference_group",
                "positive_group",
            ],
        ),

        "machine_learning": _extract_columns(
            ml_row,
            [
                "gene_name",
                "importance",
                "ML_rank",
            ],
        ),

        "stability": _extract_columns(
            stability_row,
            [
                "gene_name",
                "stability_score",
                "stability_rank",
                "top10_stability",
                "top20_stability",
                "mean_rf_importance",
                "sd_rf_importance",
                "mean_permutation_importance",
                "sd_permutation_importance",
                "normalized_rf",
                "normalized_permutation",
            ],
        ),

        "pathway": pathway_evidence,
    }

    return evidence


def evidence_exists(evidence: dict[str, Any]) -> bool:
    """Return True when at least one evidence section contains data."""

    for key, value in evidence.items():
        if key == "gene_name":
            continue

        if isinstance(value, dict) and value:
            return True

        if isinstance(value, list) and value:
            return True

    return False
