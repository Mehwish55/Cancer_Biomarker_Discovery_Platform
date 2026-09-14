from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path
from uuid import uuid4

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CUSTOMER_RESULTS_ROOT = PROJECT_ROOT / "customer_results"


def create_analysis_id() -> str:
    """Create a unique identifier for a customer analysis."""
    return uuid4().hex[:12]


def create_result_directory(analysis_id: str) -> Path:
    """Create and return the persistent directory for one analysis."""
    result_directory = CUSTOMER_RESULTS_ROOT / analysis_id
    result_directory.mkdir(parents=True, exist_ok=True)
    return result_directory


@dataclass
class CustomerAnalysisContext:
    """
    Central context for a customer-specific OncoNexa analysis.

    This keeps customer analysis separate from the existing
    LUAD reference/demo datasets.
    """

    cancer_type: str
    comparison: str
    analysis_type: str

    gene_column: Optional[str] = None
    sample_columns: list[str] = field(default_factory=list)
    groups: dict[str, str] = field(default_factory=dict)

    expression_data: Optional[pd.DataFrame] = None
    metadata: Optional[pd.DataFrame] = None

    differential_expression: Optional[pd.DataFrame] = None
    analysis_status: dict[str, str] = field(default_factory=dict)

    analysis_id: Optional[str] = None
    result_directory: Optional[str] = None

    def has_differential_expression(self) -> bool:
        """Return True when customer DE results are available."""
        return (
            self.differential_expression is not None
            and not self.differential_expression.empty
        )

    def summary(self) -> dict[str, Any]:
        """Return a compact description of the current analysis."""
        return {
            "analysis_id": self.analysis_id,
            "cancer_type": self.cancer_type,
            "comparison": self.comparison,
            "analysis_type": self.analysis_type,
            "gene_column": self.gene_column,
            "n_samples": len(self.sample_columns),
            "n_groups": len(set(self.groups.values())),
            "has_expression_data": (
                self.expression_data is not None
                and not self.expression_data.empty
            ),
            "has_metadata": (
                self.metadata is not None
                and not self.metadata.empty
            ),
            "has_differential_expression": (
                self.has_differential_expression()
            ),
            "result_directory": self.result_directory,
        }
