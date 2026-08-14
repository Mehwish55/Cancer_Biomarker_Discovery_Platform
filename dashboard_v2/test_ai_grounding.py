from core.data_loader import load_dataset
from core.evidence_engine import get_biomarker_evidence
from core.ai_grounding import build_grounded_context


DATASETS = [
    "deg",
    "top15",
    "integrated_ranking",
    "model_comparison",
    "rf_importance",
    "stability",
    "roc_results",
    "validation_ranking",
    "validation_stats",
    "go_bp",
    "go_cc",
    "go_mf",
    "kegg",
]


def load_test_data():
    data = {}

    for name in DATASETS:
        try:
            data[name] = load_dataset(name)
        except Exception:
            data[name] = None

    return data


def test_ai_grounding_for_pycr1():
    data = load_test_data()

    evidence = get_biomarker_evidence(
        data,
        "PYCR1",
    )

    grounded = build_grounded_context(
        evidence,
        "PYCR1",
    )

    assert grounded is not None
    assert grounded["gene"] == "PYCR1"
    assert grounded["evidence_available"] is True


def test_grounded_context_contains_sources():
    data = load_test_data()

    evidence = get_biomarker_evidence(
        data,
        "PYCR1",
    )

    grounded = build_grounded_context(
        evidence,
        "PYCR1",
    )

    assert isinstance(grounded["sources"], list)
    assert len(grounded["sources"]) > 0


def test_grounded_context_contains_text():
    data = load_test_data()

    evidence = get_biomarker_evidence(
        data,
        "PYCR1",
    )

    grounded = build_grounded_context(
        evidence,
        "PYCR1",
    )

    assert isinstance(grounded["context"], str)
    assert len(grounded["context"].strip()) > 0
