from core.data_loader import load_dataset
from core.evidence_engine import (
    get_biomarker_evidence,
    evidence_exists,
)


DATASETS = [
    "integrated_ranking",
    "top15",
    "roc_results",
    "validation_stats",
    "rf_importance",
    "stability",
    "deg",
]


def load_test_data():
    data = {}

    for name in DATASETS:
        try:
            data[name] = load_dataset(name)
        except Exception:
            data[name] = None

    return data


def test_biomarker_evidence_for_pycr1():
    data = load_test_data()

    evidence = get_biomarker_evidence(
        data,
        "PYCR1",
    )

    assert evidence is not None
    assert evidence["gene_name"] == "PYCR1"


def test_pycr1_evidence_exists():
    data = load_test_data()

    evidence = get_biomarker_evidence(
        data,
        "PYCR1",
    )

    assert evidence_exists(evidence) is True
