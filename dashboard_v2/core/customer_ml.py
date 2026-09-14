from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class CustomerMLError(ValueError):
    """Raised when customer ML analysis cannot be performed."""


def _find_gene_column(expression: pd.DataFrame, preferred: str | None) -> str:
    """Find the gene identifier column."""
    if preferred and preferred in expression.columns:
        return preferred

    candidates = [
        "gene",
        "gene_id",
        "gene_name",
        "symbol",
        "gene_symbol",
        "ensembl",
        "ensembl_id",
        "Gene",
    ]

    for candidate in candidates:
        if candidate in expression.columns:
            return candidate

    raise CustomerMLError(
        "A gene identifier column could not be identified."
    )


def _prepare_metadata(
    metadata: pd.DataFrame,
    sample_columns: list[str],
) -> pd.DataFrame:
    """Prepare sample metadata for the uploaded expression matrix."""
    if metadata is None or metadata.empty:
        raise CustomerMLError("Sample metadata is required for ML analysis.")

    metadata = metadata.copy()

    sample_col = next(
        (
            c
            for c in ["sample_id", "sample", "Sample", "sample_name"]
            if c in metadata.columns
        ),
        None,
    )

    group_col = next(
        (
            c
            for c in ["group", "Group", "condition", "Condition", "class"]
            if c in metadata.columns
        ),
        None,
    )

    if sample_col is None or group_col is None:
        raise CustomerMLError(
            "Metadata must contain sample and group columns."
        )

    metadata[sample_col] = metadata[sample_col].astype(str)
    metadata[group_col] = metadata[group_col].astype(str)

    metadata = metadata[
        metadata[sample_col].isin(sample_columns)
    ].copy()

    if metadata.empty:
        raise CustomerMLError(
            "No expression samples could be matched to the metadata."
        )

    groups = metadata[group_col].unique().tolist()

    if len(groups) != 2:
        raise CustomerMLError(
            "Customer ML currently requires exactly two groups."
        )

    metadata = metadata.set_index(sample_col)

    matched_samples = [
        s for s in sample_columns
        if s in metadata.index
    ]

    metadata = metadata.loc[matched_samples]

    if metadata.empty:
        raise CustomerMLError(
            "No matched samples remain after metadata alignment."
        )

    return metadata


def _candidate_genes(
    differential_expression: pd.DataFrame,
    expression: pd.DataFrame,
    gene_column: str,
) -> list[str]:
    """Return candidate genes from differential-expression results."""
    if (
        differential_expression is None
        or differential_expression.empty
    ):
        raise CustomerMLError(
            "Differential expression results are required for ML analysis."
        )

    de_gene_column = next(
        (
            c
            for c in ["gene", "gene_name", "Gene"]
            if c in differential_expression.columns
        ),
        None,
    )

    if de_gene_column is None:
        raise CustomerMLError(
            "The differential-expression results do not contain a gene column."
        )

    expression_genes = set(
        expression[gene_column].astype(str)
    )

    candidates = [
        gene
        for gene in differential_expression[de_gene_column]
        .astype(str)
        .tolist()
        if gene in expression_genes
    ]

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(candidates))


def _expression_matrix(
    expression: pd.DataFrame,
    gene_column: str,
    genes: list[str],
    sample_columns: list[str],
) -> pd.DataFrame:
    """Create a genes-by-samples matrix for ML."""
    work = expression.copy()
    work[gene_column] = work[gene_column].astype(str)

    work = work[work[gene_column].isin(genes)].copy()

    if work.empty:
        raise CustomerMLError(
            "No differential-expression candidate genes were found "
            "in the uploaded expression data."
        )

    work = work.drop_duplicates(
        subset=[gene_column],
        keep="first",
    )

    available_samples = [
        c
        for c in sample_columns
        if c in work.columns
    ]

    if len(available_samples) < 4:
        raise CustomerMLError(
            "At least four matched expression samples are required."
        )

    matrix = work.set_index(gene_column)[available_samples].apply(
        pd.to_numeric,
        errors="coerce",
    )

    matrix = matrix.replace([np.inf, -np.inf], np.nan)

    matrix = matrix.dropna(
        axis=0,
        how="any",
    )

    if matrix.empty:
        raise CustomerMLError(
            "Candidate expression values are not usable for ML analysis."
        )

    return matrix


def _build_models(random_state: int) -> dict[str, Any]:
    """Build the ML models used for customer analysis."""
    return {
        "Logistic Regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=500,
            random_state=random_state,
            class_weight="balanced",
            n_jobs=-1,
        ),
    }


def _cross_validate_models(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int,
) -> pd.DataFrame:
    """Calculate stratified cross-validated model performance."""
    class_counts = y.value_counts()

    if len(class_counts) != 2:
        raise CustomerMLError(
            "Customer ML requires exactly two classes."
        )

    min_class_count = int(class_counts.min())

    if min_class_count < 2:
        raise CustomerMLError(
            "Each group must contain at least two samples for cross-validation."
        )

    n_splits = min(5, min_class_count)

    cv = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    scoring = {
        "auc": "roc_auc",
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
    }

    rows: list[dict[str, float | str]] = []

    for model_name, model in _build_models(random_state).items():
        scores = cross_validate(
            model,
            X,
            y,
            cv=cv,
            scoring=scoring,
            error_score="raise",
        )

        rows.append(
            {
                "model": model_name,
                "AUC_mean": float(np.mean(scores["test_auc"])),
                "AUC_std": float(np.std(scores["test_auc"], ddof=1))
                if n_splits > 1
                else 0.0,
                "Accuracy_mean": float(
                    np.mean(scores["test_accuracy"])
                ),
                "Precision_mean": float(
                    np.mean(scores["test_precision"])
                ),
                "Recall_mean": float(
                    np.mean(scores["test_recall"])
                ),
                "F1_mean": float(
                    np.mean(scores["test_f1"])
                ),
                "CV_folds": n_splits,
            }
        )

    return pd.DataFrame(rows).sort_values(
        "AUC_mean",
        ascending=False,
    ).reset_index(drop=True)


def _random_forest_importance(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int,
) -> pd.DataFrame:
    """Fit Random Forest and calculate gene-level feature importance."""
    model = RandomForestClassifier(
        n_estimators=500,
        random_state=random_state,
        class_weight="balanced",
        n_jobs=-1,
    )

    model.fit(X, y)

    result = pd.DataFrame(
        {
            "gene_name": X.columns,
            "importance": model.feature_importances_,
        }
    )

    result = result.sort_values(
        "importance",
        ascending=False,
    ).reset_index(drop=True)

    result["ML_rank"] = np.arange(1, len(result) + 1)

    return result


def run_customer_ml(
    expression_data: pd.DataFrame,
    metadata: pd.DataFrame,
    differential_expression: pd.DataFrame,
    gene_column: str | None = None,
    sample_columns: list[str] | None = None,
    random_state: int = 42,
) -> dict[str, Any]:
    """
    Run customer-specific ML analysis.

    Returns:
        {
            "model_comparison": DataFrame,
            "rf_importance": DataFrame,
            "candidate_genes": list[str],
            "n_samples": int,
            "n_features": int,
            "reference_group": str,
            "positive_group": str,
        }

    ML performance is calculated using stratified cross-validation.
    Random Forest feature importance is fitted on the full uploaded
    candidate-gene dataset and should be interpreted as exploratory
    feature contribution, not independent validation.
    """
    if expression_data is None or expression_data.empty:
        raise CustomerMLError(
            "Uploaded expression data is required."
        )

    if sample_columns is None:
        sample_columns = [
            c
            for c in expression_data.columns
            if c != gene_column
        ]

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
        raise CustomerMLError(
            "At least two differential-expression candidate genes "
            "are required for ML analysis."
        )

    matrix = _expression_matrix(
        expression_data,
        gene_column,
        candidates,
        sample_columns,
    )

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
            for c in ["group", "Group", "condition", "Condition", "class"]
            if c in metadata_aligned.columns
        ),
        None,
    )

    if group_column is None:
        raise CustomerMLError(
            "A group column could not be identified in the metadata."
        )

    y_labels = metadata_aligned[group_column].astype(str)

    groups = y_labels.unique().tolist()

    if len(groups) != 2:
        raise CustomerMLError(
            "Customer ML requires exactly two groups."
        )

    # The second metadata group is treated as the positive class.
    reference_group = groups[0]
    positive_group = groups[1]

    y = (y_labels == positive_group).astype(int)

    X = matrix.T.copy()
    X.columns = X.columns.astype(str)

    # Remove zero-variance genes because they carry no predictive signal.
    variance = X.var(axis=0, ddof=0)
    X = X.loc[:, variance > 0]

    if X.shape[1] < 2:
        raise CustomerMLError(
            "At least two variable candidate genes are required "
            "for ML analysis."
        )

    model_comparison = _cross_validate_models(
        X,
        y,
        random_state,
    )

    rf_importance = _random_forest_importance(
        X,
        y,
        random_state,
    )

    return {
        "model_comparison": model_comparison,
        "rf_importance": rf_importance,
        "candidate_genes": X.columns.tolist(),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "reference_group": reference_group,
        "positive_group": positive_group,
        "cv_folds": int(
            model_comparison["CV_folds"].iloc[0]
        ),
    }
