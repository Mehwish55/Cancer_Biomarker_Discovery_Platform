import pandas as pd


def _find_gene_row(df, gene_name):
    """Return the row for a gene if the dataset contains it."""

    if df is None or df.empty:
        return None

    if "gene_name" not in df.columns:
        return None

    matches = df[
        df["gene_name"].astype(str).str.upper()
        == str(gene_name).upper()
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def _clean_value(value):
    """Convert pandas/numpy values into simple Python values."""

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return value


def _extract_columns(row, columns):
    """Extract only columns that actually exist."""

    if row is None:
        return {}

    result = {}

    for column in columns:
        if column in row.index:
            result[column] = _clean_value(row[column])

    return result


def get_biomarker_evidence(data, gene_name):
    """
    Collect evidence for a single biomarker.

    This function only retrieves information already present
    in the V1/V2 datasets. It does not calculate a new
    biological score.
    """

    integrated = data.get("integrated_ranking")
    top15 = data.get("top15")
    roc = data.get("roc_results")
    validation = data.get("validation_stats")
    ml = data.get("rf_importance")
    stability = data.get("stability")
    deg = data.get("deg")

    integrated_row = _find_gene_row(
        integrated,
        gene_name,
    )

    top15_row = _find_gene_row(
        top15,
        gene_name,
    )

    roc_row = _find_gene_row(
        roc,
        gene_name,
    )

    validation_row = _find_gene_row(
        validation,
        gene_name,
    )

    ml_row = _find_gene_row(
        ml,
        gene_name,
    )

    stability_row = _find_gene_row(
        stability,
        gene_name,
    )

    deg_row = _find_gene_row(
        deg,
        gene_name,
    )

    evidence = {
        "gene_name": gene_name,

        "integrated_ranking": _extract_columns(
            integrated_row,
            [
                "integrated_score",
                "integrated_rank",
                "score_AUC",
                "score_sensitivity",
                "score_specificity",
                "score_stability",
                "score_ML",
                "score_DE",
            ],
        ),

        "top15": _extract_columns(
            top15_row,
            [
                "validation_rank",
                "validation_status",
                "AUC",
                "stability_score",
                "ML_rank",
                "log2FoldChange",
                "padj",
            ],
        ),

        "roc_validation": _extract_columns(
            roc_row,
            [
                "AUC",
                "AUC_CI_lower",
                "AUC_CI_upper",
                "sensitivity",
                "specificity",
            ],
        ),

        "independent_validation": _extract_columns(
            validation_row,
            [
                "gene_name",
                "log2FoldChange",
                "pvalue",
                "padj",
                "direction",
                "validation_status",
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
        "differential_expression": _extract_columns(
            deg_row,
            [
                "gene_name",
                "baseMean",
                "log2FoldChange",
                "pvalue",
                "padj",
                "direction",
            ],
        ),
    }

    return evidence


def evidence_exists(evidence):
    """Return True if at least one evidence section contains data."""

    for key, value in evidence.items():

        if key == "gene_name":
            continue

        if isinstance(value, dict) and value:
            return True

    return False
