from __future__ import annotations

import numpy as np
import pandas as pd


def _auc_from_scores(y_true: np.ndarray, scores: np.ndarray) -> float:
    """
    Calculate ROC-AUC using the rank-sum / Mann-Whitney formulation.

    This implementation intentionally uses only NumPy so the customer
    ROC workflow does not require SciPy or scikit-learn.
    """
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)

    positive = scores[y_true == 1]
    negative = scores[y_true == 0]

    if len(positive) == 0 or len(negative) == 0:
        return np.nan

    combined = np.concatenate([positive, negative])
    ranks = pd.Series(combined).rank(method="average").to_numpy()

    positive_rank_sum = ranks[: len(positive)].sum()

    auc = (
        positive_rank_sum
        - len(positive) * (len(positive) + 1) / 2
    ) / (len(positive) * len(negative))

    return float(auc)


def _best_threshold(
    y_true: np.ndarray,
    scores: np.ndarray,
) -> tuple[float, float, float, float]:
    """
    Find the threshold maximizing Youden's J statistic.

    Returns:
        threshold, sensitivity, specificity, youden_j
    """
    unique_scores = np.unique(scores)

    best = None

    for threshold in unique_scores:
        predicted = scores >= threshold

        tp = np.sum((predicted == 1) & (y_true == 1))
        fn = np.sum((predicted == 0) & (y_true == 1))
        tn = np.sum((predicted == 0) & (y_true == 0))
        fp = np.sum((predicted == 1) & (y_true == 0))

        sensitivity = (
            tp / (tp + fn)
            if (tp + fn) > 0
            else np.nan
        )

        specificity = (
            tn / (tn + fp)
            if (tn + fp) > 0
            else np.nan
        )

        youden_j = sensitivity + specificity - 1

        candidate = (
            youden_j,
            threshold,
            sensitivity,
            specificity,
        )

        if best is None or candidate[0] > best[0]:
            best = candidate

    if best is None:
        return np.nan, np.nan, np.nan, np.nan

    return (
        float(best[1]),
        float(best[2]),
        float(best[3]),
        float(best[0]),
    )


def calculate_customer_roc(
    expression: pd.DataFrame,
    metadata: pd.DataFrame,
    candidates: pd.DataFrame,
    gene_column: str = "Gene",
    sample_column: str = "sample_id",
    group_column: str = "group",
) -> pd.DataFrame:
    """
    Calculate customer-dataset ROC/AUC results for DE candidate genes.

    The first two unique groups are treated as:
        group 0 = negative/reference
        group 1 = positive/case

    Candidate genes are taken from the 'gene' column of the DE results.
    """
    if expression is None or expression.empty:
        raise ValueError("Expression data are empty.")

    if metadata is None or metadata.empty:
        raise ValueError("Metadata are empty.")

    if candidates is None or candidates.empty:
        raise ValueError("Candidate biomarker results are empty.")

    required_expression = {gene_column}
    required_metadata = {sample_column, group_column}

    missing_expression = required_expression - set(expression.columns)
    missing_metadata = required_metadata - set(metadata.columns)

    if missing_expression:
        raise ValueError(
            f"Expression data are missing: "
            f"{sorted(missing_expression)}"
        )

    if missing_metadata:
        raise ValueError(
            f"Metadata are missing: "
            f"{sorted(missing_metadata)}"
        )

    if "gene" not in candidates.columns:
        raise ValueError(
            "Candidate results must contain a 'gene' column."
        )

    metadata = metadata.copy()
    metadata[sample_column] = metadata[sample_column].astype(str)
    metadata[group_column] = metadata[group_column].astype(str)

    groups = metadata[group_column].dropna().unique().tolist()

    if len(groups) != 2:
        raise ValueError(
            "Customer ROC currently requires exactly two groups."
        )

    reference_group = groups[0]
    positive_group = groups[1]

    sample_ids = metadata[sample_column].tolist()

    missing_samples = [
        sample for sample in sample_ids
        if sample not in expression.columns
    ]

    if missing_samples:
        raise ValueError(
            "Metadata samples not found in expression data: "
            + ", ".join(missing_samples)
        )

    y_true = (
        metadata[group_column]
        == positive_group
    ).astype(int).to_numpy()

    candidate_genes = (
        candidates["gene"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    expression_index = (
        expression[gene_column]
        .astype(str)
    )

    rows = []

    for gene in candidate_genes:

        matches = expression_index == gene

        if not matches.any():
            continue

        gene_row = expression.loc[matches].iloc[0]

        values = pd.to_numeric(
            gene_row[sample_ids],
            errors="coerce",
        ).to_numpy(dtype=float)

        valid = np.isfinite(values)

        if valid.sum() < 4:
            continue

        gene_y = y_true[valid]
        gene_scores = values[valid]

        if len(np.unique(gene_y)) != 2:
            continue

        auc_forward = _auc_from_scores(
            gene_y,
            gene_scores,
        )

        # If lower expression is associated with the positive group,
        # reverse the score direction so AUC represents discrimination
        # in the positive/case direction.
        if auc_forward < 0.5:
            auc = _auc_from_scores(
                gene_y,
                -gene_scores,
            )
            threshold, sensitivity, specificity, youden_j = (
                _best_threshold(
                    gene_y,
                    -gene_scores,
                )
            )
            direction = "Lower in positive group"
        else:
            auc = auc_forward
            threshold, sensitivity, specificity, youden_j = (
                _best_threshold(
                    gene_y,
                    gene_scores,
                )
            )
            direction = "Higher in positive group"

        rows.append(
            {
                "gene_name": gene,
                "AUC": auc,
                "CI_lower": np.nan,
                "CI_upper": np.nan,
                "pvalue": np.nan,
                "sensitivity": sensitivity,
                "specificity": specificity,
                "threshold": threshold,
                "direction": direction,
                "reference_group": reference_group,
                "positive_group": positive_group,
            }
        )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    result = result.sort_values(
        ["AUC", "gene_name"],
        ascending=[False, True],
    ).reset_index(drop=True)

    result.insert(
        0,
        "ROC_rank",
        np.arange(1, len(result) + 1),
    )

    return result
