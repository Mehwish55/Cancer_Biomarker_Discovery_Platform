from pathlib import Path
from typing import Any

import pandas as pd
import yaml
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_FILE = PROJECT_ROOT / "dashboard_v2" / "config" / "data_manifest.yaml"


class DataLoadError(Exception):
    """Raised when a configured dataset cannot be loaded."""
    pass


@st.cache_data
def load_manifest() -> dict[str, Any]:
    """Load the V2 dataset manifest."""
    if not MANIFEST_FILE.exists():
        raise DataLoadError(
            f"Data manifest not found: {MANIFEST_FILE}"
        )

    with open(MANIFEST_FILE, "r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file)

    if not isinstance(manifest, dict):
        raise DataLoadError("Invalid data manifest format.")

    return manifest


def get_dataset_config(dataset_name: str) -> dict[str, Any]:
    """Return configuration for a dataset."""
    manifest = load_manifest()

    datasets = manifest.get("datasets", {})

    if dataset_name not in datasets:
        raise DataLoadError(
            f"Dataset '{dataset_name}' is not defined in the manifest."
        )

    return datasets[dataset_name]


@st.cache_data
def load_dataset(dataset_name: str) -> pd.DataFrame:
    """
    Load a configured CSV dataset.

    The path is resolved relative to the project root.
    """

    config = get_dataset_config(dataset_name)

    relative_path = config.get("path")

    if not relative_path:
        raise DataLoadError(
            f"No path configured for dataset '{dataset_name}'."
        )

    file_path = PROJECT_ROOT / relative_path

    if not file_path.exists():
        raise DataLoadError(
            f"Dataset '{dataset_name}' was not found:\n{file_path}"
        )

    try:
        dataframe = pd.read_csv(file_path)
    except Exception as exc:
        raise DataLoadError(
            f"Could not read dataset '{dataset_name}': {exc}"
        ) from exc

    if dataframe.empty:
        return dataframe

    expected_rows = config.get("expected_rows")

    if expected_rows is not None:
        if len(dataframe) != expected_rows:
            raise DataLoadError(
                f"Dataset '{dataset_name}' has {len(dataframe)} rows "
                f"but expected {expected_rows}.\n"
                f"File: {file_path}"
            )

    return dataframe


def get_dataset_metadata(dataset_name: str) -> dict[str, Any]:
    """Return manifest metadata for a dataset."""

    config = get_dataset_config(dataset_name)

    relative_path = config.get("path")
    file_path = PROJECT_ROOT / relative_path

    metadata = {
        "dataset": dataset_name,
        "path": str(relative_path),
        "absolute_path": str(file_path),
        "stage": config.get("stage"),
        "gene_universe": config.get("gene_universe"),
        "join_key": config.get("join_key"),
        "exists": file_path.exists(),
    }

    if file_path.exists():
        metadata["modified"] = file_path.stat().st_mtime

    return metadata


def validate_required_columns(
    dataframe: pd.DataFrame,
    dataset_name: str,
    required_columns: list[str],
) -> None:
    """Validate that required columns exist."""

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise DataLoadError(
            f"Dataset '{dataset_name}' is missing required columns: "
            f"{', '.join(missing_columns)}"
        )


def clear_dataset_cache() -> None:
    """Clear cached datasets."""

    load_manifest.clear()
    load_dataset.clear()
