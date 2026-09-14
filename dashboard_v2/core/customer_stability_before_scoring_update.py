from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance

from core.customer_ml import (
    CustomerMLError,
    _candidate_genes,
    _expression_matrix,
    _find_gene_column,
    _prepare_metadata,
)


class CustomerStabilityError(ValueError):
    """Raised when customer stability analysis cannot be performed."""


def _rank_series(values: pd.Series) -> pd.Series:
    """Return descending ranks with deterministic average ranking."""
    return values.rank(
        ascending=False,
        method="average",
    )


def run_customer_stability(
    expression_data: pd.DataFrame,
    metadata: pd.DataFrame,
    differential_expression: pd.DataFrame,
    gene_column: str | None = None,
    sample_columns: list[str] | None = None,
    n_iterations: int = 50,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Calculate exploratory biomarker stability from repeated resampling.

    The analysis uses differential-expression candidate genes and repeatedly
    resamples samples within each group. A Random Forest is fitted on each
    resampled dataset, followed by permutation importance on that resample.

    Returns:
        {
            "stability": DataFrame,
            "n_iterations": int,
            "n_samples": int,
            "n_features": int,
            "reference_group": str,
            "positive_group": str,
        }

    This is within-dataset exploratory evidence and is not independent
    validation or clinical validation.
    """
    if expression_data is None or expression_data.empty:
        raise CustomerStabilityError(
            "Uploaded expression data is required."
        )

    if metadata is None or metadata.empty:
        raise CustomerStabilityError(
            "Sample metadata is required for stability analysis."
        )

    if differential_expression is None or differential_expression.empty:
        raise CustomerStabilityError(
            "Differential expression results are required for stability analysis."
        )

    if n_iterations < 10:
        raise CustomerStabilityError(
            "At least 10 stability iterations are required."
        )

    if sample_columns is None:
        sample_columns = [
            c for c in expression_data.columns
            if c != gene_column
        ]

    try:
        gene_column = _find_gene_column(
            expression_data,
            gene_column,
        )

        metadata_aligned = _prepare_metadata(
            metadata,
            sample_columns,
        )

        candidates = _candidate_genes(
            differential_expression,
            expression_data,
            gene_column,
        )

        if len(candidates) < 2:
            raise CustomerStabilityError(
                "At least two differential-expression candidate genes "
                "are required for stability analysis."
            )

        matrix = _expression_matrix(
            expression_data,
            gene_column,
            candidates,
            sample_columns,
        )

    except CustomerMLError as exc:
        raise CustomerStabilityError(str(exc)) from exc

    matched_samples = [
        sample
        for sample in matrix.columns
        if sample in metadata_aligned.index
    ]

    matrix = matrix[matched_samples]
    metadata_aligned = metadata_aligned.loc[matched_samples]

    group_column = next(
        (
            c
            for c in [
                "group",
                "Group",
                "condition",
                "Condition",
                "class",
            ]
            if c in metadata_aligned.columns
        ),
        None,
    )

    if group_column is None:
        raise CustomerStabilityError(
            "A group column could not be identified in the metadata."
        )

    y_labels = metadata_aligned[group_column].astype(str)
    groups = y_labels.unique().tolist()

    if len(groups) != 2:
        raise CustomerStabilityError(
            "Customer stability analysis requires exactly two groups."
        )

    reference_group = groups[0]
    positive_group = groups[1]

    y = (y_labels == positive_group).astype(int)

    X = matrix.T.copy()
    X.columns = X.columns.astype(str)

    variance = X.var(axis=0, ddof=0)
    X = X.loc[:, variance > 0]

    if X.shape[1] < 2:
        raise CustomerStabilityError(
            "At least two variable candidate genes are required "
            "for stability analysis."
        )

    if len(X) < 6:
        raise CustomerStabilityError(
            "At least six samples are required for stability analysis."
        )

    class_counts = y.value_counts()

    if len(class_counts) != 2 or int(class_counts.min()) < 2:
        raise CustomerStabilityError(
            "Each group must contain at least two samples."
        )

    rng = np.random.default_rng(random_state)

    rf_importance_rows: list[pd.Series] = []
    permutation_importance_rows: list[pd.Series] = []
    rf_rank_rows: list[pd.Series] = []
    permutation_rank_rows: list[pd.Series] = []
    top10_selections: dict[str, int] = {gene: 0 for gene in X.columns}
    top20_selections: dict[str, int] = {gene: 0 for gene in X.columns}

    n_samples_per_group = {
        group: int((y_labels == group).sum())
        for group in groups
    }

    for iteration in range(n_iterations):
        sampled_indices: list[int] = []

        for group in groups:
            group_indices = np.flatnonzero(
                y_labels.to_numpy() == group
            )

            sampled = rng.choice(
                group_indices,
                size=n_samples_per_group[group],
                replace=True,
            )

            sampled_indices.extend(sampled.tolist())

        X_resampled = X.iloc[sampled_indices].copy()
        y_resampled = y.iloc[sampled_indices].copy()

        if y_resampled.nunique() != 2:
            continue

        model = RandomForestClassifier(
            n_estimators=300,
            random_state=random_state + iteration,
            class_weight="balanced",
            n_jobs=-1,
        )

        model.fit(
            X_resampled,
            y_resampled,
        )

        rf_values = pd.Series(
            model.feature_importances_,
            index=X.columns,
            dtype=float,
        )

        rf_ranks = _rank_series(rf_values)

        permutation = permutation_importance(
            model,
            X_resampled,
            y_resampled,
            scoring="roc_auc",
            n_repeats=5,
            random_state=random_state + iteration,
            n_jobs=-1,
        )

        permutation_values = pd.Series(
            permutation.importances_mean,
            index=X.columns,
            dtype=float,
        )

        permutation_ranks = _rank_series(
            permutation_values,
        )

        rf_importance_rows.append(rf_values)
        permutation_importance_rows.append(permutation_values)
        rf_rank_rows.append(rf_ranks)
        permutation_rank_rows.append(permutation_ranks)

        top10 = rf_values.nlargest(
            min(10, len(rf_values))
        ).index

        top20 = rf_values.nlargest(
            min(20, len(rf_values))
        ).index

        for gene in top10:
            top10_selections[gene] += 1

        for gene in top20:
            top20_selections[gene] += 1

    completed_iterations = len(rf_importance_rows)

    if completed_iterations < max(10, n_iterations // 2):
        raise CustomerStabilityError(
            "Too few successful resampling iterations were completed "
            "to calculate reliable stability estimates."
        )

    rf_df = pd.DataFrame(
        rf_importance_rows
    )

    permutation_df = pd.DataFrame(
        permutation_importance_rows
    )

    rf_rank_df = pd.DataFrame(
        rf_rank_rows
    )

    permutation_rank_df = pd.DataFrame(
        permutation_rank_rows
    )

    result = pd.DataFrame(
        {
            "gene_name": X.columns,
            "mean_rf_importance": rf_df.mean(),
            "sd_rf_importance": rf_df.std(
                ddof=1
            ),
            "mean_permutation_importance": (
                permutation_df.mean()
            ),
            "sd_permutation_importance": (
                permutation_df.std(ddof=1)
            ),
            "mean_rf_rank": rf_rank_df.mean(),
            "mean_permutation_rank": (
                permutation_rank_df.mean()
            ),
            "top10_folds": [
                top10_selections[gene]
                for gene in X.columns
            ],
            "top20_folds": [
                top20_selections[gene]
                for gene in X.columns
            ],
        }
    )

    result["top10_stability"] = (
        result["top10_folds"] / completed_iterations
    )

    result["top20_stability"] = (
        result["top20_folds"] / completed_iterations
    )

    rf_max = result["mean_rf_importance"].max()

    if rf_max > 0:
        result["normalized_rf"] = (
            result["mean_rf_importance"] / rf_max
        )
    else:
        result["normalized_rf"] = 0.0

    permutation_values = result[
        "mean_permutation_importance"
    ].clip(lower=0)

    permutation_max = permutation_values.max()

    if permutation_max > 0:
        result["normalized_permutation"] = (
            permutation_values / permutation_max
        )
    else:
        result["normalized_permutation"] = 0.0

    result["stability_score"] = (
        0.30 * result["normalized_rf"]
        + 0.20 * result["normalized_permutation"]
        + 0.30 * result["top10_stability"]
        + 0.20 * result["top20_stability"]
    )

    result = result.sort_values(
        [
            "stability_score",
            "top10_stability",
            "mean_rf_importance",
        ],
        ascending=False,
    ).reset_index(drop=True)

    result["stability_rank"] = np.arange(
        1,
        len(result) + 1,
    )

    return {
        "stability": result,
        "n_iterations": completed_iterations,
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "reference_group": reference_group,
        "positive_group": positive_group,
    }
