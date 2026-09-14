from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass
class UserDataValidation:
    """Validation result for user-provided expression and metadata."""

    valid: bool
    messages: list[str]
    warnings: list[str]
    expression_format: Optional[str] = None
    n_genes: int = 0
    n_samples: int = 0
    n_metadata_samples: int = 0
    matched_samples: int = 0
    groups: list[str] | None = None


def detect_expression_format(df: pd.DataFrame) -> str:
    """
    Detect whether an expression dataframe is wide or long format.

    Supported formats:

    Wide:
        gene/sample columns with one row per gene.

    Long:
        sample_id + gene identifier + expression value.
    """

    columns = {str(column).strip().lower() for column in df.columns}

    long_sample_columns = {
        "sample_id",
        "sample",
        "sampleid",
    }

    long_gene_columns = {
        "gene",
        "gene_id",
        "gene_name",
        "geneid",
    }

    expression_columns = {
        "count",
        "expression",
        "value",
        "normalized_count",
        "fpkm",
        "tpm",
    }

    if (
        columns.intersection(long_sample_columns)
        and columns.intersection(long_gene_columns)
        and columns.intersection(expression_columns)
    ):
        return "long"

    if len(df.columns) >= 3:
        return "wide"

    return "unknown"


def _find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]

    return None


def validate_user_data(
    expression_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
) -> UserDataValidation:

    messages: list[str] = []
    warnings: list[str] = []

    if expression_df is None or expression_df.empty:
        return UserDataValidation(
            valid=False,
            messages=["Expression data is empty."],
            warnings=[],
        )

    if metadata_df is None or metadata_df.empty:
        return UserDataValidation(
            valid=False,
            messages=["Metadata is empty."],
            warnings=[],
        )

    expression_format = detect_expression_format(expression_df)

    if expression_format == "unknown":
        return UserDataValidation(
            valid=False,
            messages=[
                "Could not recognize the expression-data format."
            ],
            warnings=[],
        )

    metadata_sample_column = _find_column(
        metadata_df,
        ["sample_id", "sample", "sampleid"],
    )

    metadata_group_column = _find_column(
        metadata_df,
        ["group", "condition", "class", "status"],
    )

    if metadata_sample_column is None:
        messages.append(
            "Metadata must contain a sample identifier column "
            "(for example: sample_id)."
        )

    if metadata_group_column is None:
        messages.append(
            "Metadata must contain a group/condition column "
            "(for example: group)."
        )

    if messages:
        return UserDataValidation(
            valid=False,
            messages=messages,
            warnings=warnings,
            expression_format=expression_format,
        )

    if expression_format == "long":

        sample_column = _find_column(
            expression_df,
            ["sample_id", "sample", "sampleid"],
        )

        gene_column = _find_column(
            expression_df,
            ["gene_name", "gene", "gene_id", "geneid"],
        )

        value_column = _find_column(
            expression_df,
            [
                "count",
                "expression",
                "value",
                "normalized_count",
                "fpkm",
                "tpm",
            ],
        )

        if sample_column is None:
            messages.append(
                "Long-format expression data needs a sample identifier."
            )

        if gene_column is None:
            messages.append(
                "Long-format expression data needs a gene identifier."
            )

        if value_column is None:
            messages.append(
                "Long-format expression data needs an expression-value "
                "column."
            )

        if messages:
            return UserDataValidation(
                valid=False,
                messages=messages,
                warnings=warnings,
                expression_format=expression_format,
            )

        expression_samples = set(
            expression_df[sample_column]
            .dropna()
            .astype(str)
        )

        genes = expression_df[gene_column].dropna().astype(str)

        n_genes = genes.nunique()
        n_samples = expression_samples.__len__()

        if expression_df[value_column].isna().any():
            warnings.append(
                "Expression data contains missing expression values."
            )

    else:

        gene_column = _find_column(
            expression_df,
            ["gene", "gene_name", "gene_id", "geneid"],
        )

        if gene_column is None:
            gene_column = expression_df.columns[0]

        sample_columns = [
            column
            for column in expression_df.columns
            if column != gene_column
        ]

        expression_samples = set(
            str(column)
            for column in sample_columns
        )

        genes = expression_df[gene_column].dropna().astype(str)

        n_genes = genes.nunique()
        n_samples = len(sample_columns)

        if expression_df[gene_column].duplicated().any():
            warnings.append(
                "Expression data contains duplicated gene identifiers."
            )

    metadata_samples = set(
        metadata_df[metadata_sample_column]
        .dropna()
        .astype(str)
    )

    matched_samples = len(
        expression_samples.intersection(metadata_samples)
    )

    missing_metadata = expression_samples - metadata_samples
    extra_metadata = metadata_samples - expression_samples

    if missing_metadata:
        messages.append(
            f"{len(missing_metadata)} expression samples are missing "
            "from the metadata."
        )

    if extra_metadata:
        warnings.append(
            f"{len(extra_metadata)} metadata samples are not present "
            "in the expression data."
        )

    groups = sorted(
        metadata_df[metadata_group_column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if len(groups) < 2:
        messages.append(
            "At least two experimental groups are required "
            "for comparative analysis."
        )

    if len(groups) > 10:
        warnings.append(
            "More than 10 groups were detected. "
            "The first analysis version is designed primarily "
            "for simpler comparative experiments."
        )

    if matched_samples < 2:
        messages.append(
            "Fewer than two expression samples match the metadata."
        )

    valid = len(messages) == 0

    if valid:
        messages.append(
            "Expression data and metadata are compatible."
        )

    return UserDataValidation(
        valid=valid,
        messages=messages,
        warnings=warnings,
        expression_format=expression_format,
        n_genes=n_genes,
        n_samples=n_samples,
        n_metadata_samples=len(metadata_samples),
        matched_samples=matched_samples,
        groups=groups,
    )
