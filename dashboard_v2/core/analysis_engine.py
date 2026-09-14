from __future__ import annotations

from pathlib import Path
import subprocess

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
R_SCRIPT = PROJECT_ROOT / "analysis_engine" / "generic_differential_expression.R"


class AnalysisEngineError(RuntimeError):
    """Raised when the generic analysis engine cannot complete."""


def run_differential_expression(
    expression_file: str | Path,
    metadata_file: str | Path,
    expression_type: str,
    output_file: str | Path,
) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Run the generic R differential-expression engine.

    Parameters
    ----------
    expression_file:
        Path to the uploaded expression CSV.
    metadata_file:
        Path to the uploaded metadata CSV.
    expression_type:
        Either "raw counts" or "normalized".
    output_file:
        Path where standardized results should be written.

    Returns
    -------
    results:
        Standardized differential-expression results.
    status:
        Analysis status information read from the R status file.
    """

    expression_file = Path(expression_file).resolve()
    metadata_file = Path(metadata_file).resolve()
    output_file = Path(output_file).resolve()

    if not expression_file.exists():
        raise AnalysisEngineError(
            f"Expression file not found: {expression_file}"
        )

    if not metadata_file.exists():
        raise AnalysisEngineError(
            f"Metadata file not found: {metadata_file}"
        )

    if not R_SCRIPT.exists():
        raise AnalysisEngineError(
            f"R analysis script not found: {R_SCRIPT}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "Rscript",
        str(R_SCRIPT),
        str(expression_file),
        str(metadata_file),
        expression_type,
        str(output_file),
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise AnalysisEngineError(
            f"Could not start Rscript: {exc}"
        ) from exc

    if completed.returncode != 0:
        error_message = completed.stderr.strip()

        if not error_message:
            error_message = completed.stdout.strip()

        raise AnalysisEngineError(
            "Differential-expression analysis failed.\n"
            f"{error_message}"
        )

    if not output_file.exists():
        raise AnalysisEngineError(
            "R analysis completed, but the expected results file "
            f"was not created: {output_file}"
        )

    status_file = Path(
        f"{output_file.with_suffix('')}_status.txt"
    )

    if not status_file.exists():
        raise AnalysisEngineError(
            "R analysis completed, but the expected status file "
            f"was not created: {status_file}"
        )

    results = pd.read_csv(output_file)

    status_lines = status_file.read_text(
        encoding="utf-8"
    ).splitlines()

    status: dict[str, str] = {}

    for line in status_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            status[key.strip()] = value.strip()

    return results, status
