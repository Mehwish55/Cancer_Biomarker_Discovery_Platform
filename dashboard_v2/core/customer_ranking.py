from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class CustomerRankingError(ValueError):
    """Raised when customer integrated ranking cannot be calculated."""


def _find_column(
    dataframe: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    for column in candidates:
        if column in dataframe.columns:
            return column
    return None


def _minmax(series: pd.Series) -> pd.Series:
    """Normalize a numeric series to 0-1."""
    values = pd.to_numeric(series, errors="coerce")

    if values.notna().sum() == 0:
        return pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

    minimum = values.min()
    maximum = values.max()

    if not np.isfinite(minimum) or not np.isfinite(maximum):
        return pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

    if maximum == minimum:
        return pd.Series(
            1.0,
            index=series.index,
            dtype=float,
        )

    return (values - minimum) / (maximum - minimum)


def _rank_score(
    series: pd.Series,
    ascending: bool = False,
) -> pd.Series:
    """Convert ranking information into a 0-1 score."""
    numeric = pd.to_numeric(series, errors="coerce")

    if numeric.notna().sum() == 0:
        return pd.Series(
            np.nan,
            index=series.index,
            dtype=float,
        )

    ranks = numeric.rank(
        ascending=ascending,
        method="average",
    )

    if len(ranks) <= 1:
        return pd.Series(
            1.0,
            index=series.index,
            dtype=float,
        )

    return 1.0 - (
        (ranks - 1.0)
        / (len(ranks) - 1.0)
    )


def _de_score(
    differential_expression: pd.DataFrame,
) -> pd.DataFrame:
    """Create a robust gene-level DE evidence score."""
    if differential_expression is None or differential_expression.empty:
        return pd.DataFrame(
            columns=["gene_name", "score_DE"]
        )

    gene_column = _find_column(
        differential_expression,
        ["gene", "gene_name", "Gene"],
    )

    if gene_column is None:
        return pd.DataFrame(
            columns=["gene_name", "score_DE"]
        )

    work = differential_expression.copy()
    work["gene_name"] = (
        work[gene_column]
        .astype(str)
        .str.strip()
    )

    work = work[
        work["gene_name"].notna()
        & (work["gene_name"] != "")
        & (work["gene_name"] != "nan")
    ].copy()

    if work.empty:
        return pd.DataFrame(
            columns=["gene_name", "score_DE"]
        )

    padj_column = _find_column(
        work,
        [
            "padj",
            "adj_pvalue",
            "adjusted_pvalue",
            "FDR",
            "fdr",
            "p_adj",
        ],
    )

    effect_column = _find_column(
        work,
        [
            "log2FoldChange",
            "log2FC",
            "logFC",
            "effect_size",
        ],
    )

    if padj_column is not None:
        padj = pd.to_numeric(
            work[padj_column],
            errors="coerce",
        ).clip(lower=1e-300)

        significance = (
            -np.log10(padj)
        )

        significance_score = _minmax(
            significance
        )
    else:
        significance_score = pd.Series(
            np.nan,
            index=work.index,
            dtype=float,
        )

    if effect_column is not None:
        effect = pd.to_numeric(
            work[effect_column],
            errors="coerce",
        ).abs()

        effect_score = _minmax(effect)
    else:
        effect_score = pd.Series(
            np.nan,
            index=work.index,
            dtype=float,
        )

    components = pd.concat(
        [
            significance_score.rename("significance"),
            effect_score.rename("effect"),
        ],
        axis=1,
    )

    work["score_DE"] = components.mean(
        axis=1,
        skipna=True,
    )

    work = work[
        ["gene_name", "score_DE"]
    ].drop_duplicates(
        subset=["gene_name"],
        keep="first",
    )

    return work


def _pathway_gene_scores(
    pathway_result: dict[str, Any] | None,
) -> pd.DataFrame:
    """
    Convert GO enrichment evidence into gene-level functional evidence.

    A gene receives evidence when it contributes to an enriched GO term.
    The strongest significant term contribution is retained.
    """
    if not pathway_result:
        return pd.DataFrame(
            columns=["gene_name", "score_pathway"]
        )

    frames = []

    for ontology in ["BP", "CC", "MF"]:
        table = pathway_result.get(
            ontology,
            pd.DataFrame(),
        )

        if table is None or table.empty:
            continue

        work = table.copy()

        if "contributing_genes" not in work.columns:
            continue

        padj_column = _find_column(
            work,
            ["padj", "p.adjust", "pvalue"],
        )

        enrichment_column = _find_column(
            work,
            ["FoldEnrichment", "fold_enrichment"],
        )

        if padj_column is None:
            continue

        work["_padj"] = pd.to_numeric(
            work[padj_column],
            errors="coerce",
        ).clip(lower=1e-300)

        work["_significance"] = (
            -np.log10(work["_padj"])
        )

        if enrichment_column is not None:
            work["_enrichment"] = pd.to_numeric(
                work[enrichment_column],
                errors="coerce",
            )
        else:
            work["_enrichment"] = 1.0

        work["_term_score"] = (
            _minmax(work["_significance"])
            * 0.7
            + _minmax(work["_enrichment"])
            * 0.3
        )

        for _, row in work.iterrows():
            genes = str(
                row.get("contributing_genes", "")
            )

            if not genes or genes == "nan":
                continue

            for gene in genes.split(","):
                gene = gene.strip()

                if not gene:
                    continue

                frames.append(
                    {
                        "gene_name": gene,
                        "pathway_term_score": float(
                            row["_term_score"]
                        )
                        if pd.notna(row["_term_score"])
                        else np.nan,
                    }
                )

    if not frames:
        return pd.DataFrame(
            columns=["gene_name", "score_pathway"]
        )

    work = pd.DataFrame(frames)

    result = (
        work.groupby("gene_name", as_index=False)[
            "pathway_term_score"
        ]
        .max()
        .rename(
            columns={
                "pathway_term_score": "score_pathway"
            }
        )
    )

    result["score_pathway"] = result[
        "score_pathway"
    ].clip(0.0, 1.0)

    return result


def calculate_customer_integrated_ranking(
    differential_expression: pd.DataFrame,
    roc_results: pd.DataFrame | None = None,
    ml_results: dict[str, Any] | None = None,
    stability_results: dict[str, Any] | None = None,
    pathway_results: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Calculate an evidence-based integrated ranking for one
    customer-specific cancer analysis.

    Evidence components:

        DE evidence          20%
        ROC discrimination   30%
        ML evidence          15%
        Stability            20%
        Functional biology   15%

    ROC discrimination is the mean of:
        AUC
        sensitivity
        specificity

    Missing evidence components are excluded and the remaining
    weights are renormalized automatically.
    """
    de = _de_score(
        differential_expression
    )

    if de.empty:
        raise CustomerRankingError(
            "No differential-expression candidates are available "
            "for integrated ranking."
        )

    ranking = de.copy()

    # ---------------------------------------------------------
    # ROC evidence
    # ---------------------------------------------------------

    if roc_results is not None and not roc_results.empty:
        roc = roc_results.copy()

        gene_column = _find_column(
            roc,
            ["gene_name", "gene", "Gene"],
        )

        if gene_column is not None:
            roc["gene_name"] = (
                roc[gene_column]
                .astype(str)
                .str.strip()
            )

            roc_components = []

            for column in [
                "AUC",
                "sensitivity",
                "specificity",
            ]:
                if column in roc.columns:
                    roc_components.append(
                        pd.to_numeric(
                            roc[column],
                            errors="coerce",
                        ).clip(0.0, 1.0)
                    )

            if roc_components:
                roc["score_ROC"] = pd.concat(
                    roc_components,
                    axis=1,
                ).mean(
                    axis=1,
                    skipna=True,
                )

                roc_keep = roc[
                    ["gene_name", "AUC",
                     "sensitivity",
                     "specificity",
                     "score_ROC"]
                ].drop_duplicates(
                    subset=["gene_name"]
                )

                ranking = ranking.merge(
                    roc_keep,
                    on="gene_name",
                    how="left",
                )

    # ---------------------------------------------------------
    # ML evidence
    # ---------------------------------------------------------

    if ml_results:
        ml = ml_results.get(
            "rf_importance",
            pd.DataFrame(),
        )

        if ml is not None and not ml.empty:
            ml = ml.copy()

            gene_column = _find_column(
                ml,
                ["gene_name", "gene", "Gene"],
            )

            if gene_column is not None:
                ml["gene_name"] = (
                    ml[gene_column]
                    .astype(str)
                    .str.strip()
                )

                if "importance" in ml.columns:
                    ml["score_ML"] = _minmax(
                        ml["importance"]
                    )
                elif "ML_rank" in ml.columns:
                    ml["score_ML"] = _rank_score(
                        ml["ML_rank"],
                        ascending=True,
                    )

                ml_columns = ["gene_name"]

                for column in [
                    "importance",
                    "ML_rank",
                    "score_ML",
                ]:
                    if column in ml.columns:
                        ml_columns.append(column)

                ranking = ranking.merge(
                    ml[ml_columns].drop_duplicates(
                        subset=["gene_name"]
                    ),
                    on="gene_name",
                    how="left",
                )

    # ---------------------------------------------------------
    # Stability evidence
    # ---------------------------------------------------------

    if stability_results:
        stability = stability_results.get(
            "stability",
            pd.DataFrame(),
        )

        if stability is not None and not stability.empty:
            stability = stability.copy()

            gene_column = _find_column(
                stability,
                ["gene_name", "gene", "Gene"],
            )

            if gene_column is not None:
                stability["gene_name"] = (
                    stability[gene_column]
                    .astype(str)
                    .str.strip()
                )

                if "stability_score" in stability.columns:
                    stability["score_stability"] = pd.to_numeric(
                        stability["stability_score"],
                        errors="coerce",
                    ).clip(0.0, 1.0)

                elif {
                    "normalized_rf",
                    "normalized_permutation",
                }.issubset(stability.columns):
                    stability["score_stability"] = (
                        pd.to_numeric(
                            stability["normalized_rf"],
                            errors="coerce",
                        )
                        + pd.to_numeric(
                            stability["normalized_permutation"],
                            errors="coerce",
                        )
                    ) / 2.0

                elif "top20_stability" in stability.columns:
                    stability["score_stability"] = (
                        pd.to_numeric(
                            stability["top20_stability"],
                            errors="coerce",
                        ).clip(0.0, 1.0)
                    )

                if "score_stability" in stability.columns:
                    ranking = ranking.merge(
                        stability[
                            [
                                "gene_name",
                                "score_stability",
                            ]
                        ].drop_duplicates(
                            subset=["gene_name"]
                        ),
                        on="gene_name",
                        how="left",
                    )

    # ---------------------------------------------------------
    # Functional biology evidence
    # ---------------------------------------------------------

    pathway_scores = _pathway_gene_scores(
        pathway_results
    )

    if not pathway_scores.empty:
        ranking = ranking.merge(
            pathway_scores,
            on="gene_name",
            how="left",
        )

    # ---------------------------------------------------------
    # Calculate final weighted score
    # ---------------------------------------------------------

    evidence_columns = {
        "score_DE": 0.20,
        "score_ROC": 0.30,
        "score_ML": 0.15,
        "score_stability": 0.20,
        "score_pathway": 0.15,
    }

    available_weights = {}

    for column, weight in evidence_columns.items():
        if column in ranking.columns:
            if ranking[column].notna().any():
                available_weights[column] = weight

    if not available_weights:
        raise CustomerRankingError(
            "No usable evidence components are available "
            "for integrated ranking."
        )

    total_weight = sum(
        available_weights.values()
    )

    weighted_score = pd.Series(
        0.0,
        index=ranking.index,
    )

    for column, weight in available_weights.items():
        values = pd.to_numeric(
            ranking[column],
            errors="coerce",
        )

        weighted_score += (
            values.fillna(0.0)
            * weight
            / total_weight
        )

    ranking["integrated_score"] = (
        weighted_score.clip(0.0, 1.0)
    )

    ranking = ranking.sort_values(
        [
            "integrated_score",
            "gene_name",
        ],
        ascending=[
            False,
            True,
        ],
    ).reset_index(drop=True)

    ranking.insert(
        0,
        "integrated_rank",
        np.arange(
            1,
            len(ranking) + 1,
        ),
    )

    # Keep the final table clean and predictable.
    preferred_columns = [
        "integrated_rank",
        "gene_name",
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
    ]

    # Provide individual ROC component scores for the UI.
    if "AUC" in ranking.columns:
        ranking["score_AUC"] = pd.to_numeric(
            ranking["AUC"],
            errors="coerce",
        ).clip(0.0, 1.0)

    if "sensitivity" in ranking.columns:
        ranking["score_sensitivity"] = pd.to_numeric(
            ranking["sensitivity"],
            errors="coerce",
        ).clip(0.0, 1.0)

    if "specificity" in ranking.columns:
        ranking["score_specificity"] = pd.to_numeric(
            ranking["specificity"],
            errors="coerce",
        ).clip(0.0, 1.0)

    ordered = [
        column
        for column in preferred_columns
        if column in ranking.columns
    ]

    remaining = [
        column
        for column in ranking.columns
        if column not in ordered
    ]

    return ranking[
        ordered + remaining
    ]
