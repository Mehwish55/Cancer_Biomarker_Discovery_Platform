from core.data_loader import load_dataset


REQUIRED_DATASETS = [
    "deg",
    "top15",
    "integrated_ranking",
    "model_comparison",
    "rf_importance",
    "stability",
    "roc_results",
    "validation_ranking",
    "validation_stats",
]


ENRICHMENT_DATASETS = [
    "go_bp",
    "go_cc",
    "go_mf",
    "kegg",
]


def test_required_datasets_load():
    for name in REQUIRED_DATASETS:
        df = load_dataset(name)

        assert df is not None
        assert not df.empty, f"{name} is empty"


def test_enrichment_datasets_load():
    for name in ENRICHMENT_DATASETS:
        df = load_dataset(name)

        assert df is not None


def test_kegg_dataset_schema():
    df = load_dataset("kegg")

    assert df is not None

    required_columns = [
        "ID",
        "Description",
        "GeneRatio",
        "BgRatio",
        "pvalue",
        "p.adjust",
        "qvalue",
        "geneID",
        "Count",
    ]

    for column in required_columns:
        assert column in df.columns, (
            f"KEGG is missing required column: {column}"
        )
