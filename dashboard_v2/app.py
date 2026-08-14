import streamlit as st
import pandas as pd

from core.data_loader import load_dataset
from views.biomarker_explorer import show_biomarker_explorer
from views.evidence_explorer import show_evidence_explorer
from views.ai_assistant import show_ai_assistant
from views.machine_learning import show_machine_learning
from views.stability import show_stability
from views.pathway_analysis import show_pathway_analysis
from views.integrated_ranking import show_integrated_ranking
from views.differential_expression import show_differential_expression
from views.roc_validation import show_roc_validation

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="LUAD Cancer Biomarker AI — V2",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# DATA LOADING
# ==================================================

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


@st.cache_data
def load_all_data():

    loaded = {}
    errors = {}

    for name in DATASETS:

        try:
            loaded[name] = load_dataset(name)

        except Exception as exc:
            loaded[name] = None
            errors[name] = str(exc)

    return loaded, errors


data, errors = load_all_data()

# ==================================================
# DATA OBJECTS
# ==================================================

deg = data.get("deg")
top15 = data.get("top15")
ranking = data.get("integrated_ranking")
model_comparison = data.get("model_comparison")
rf_importance = data.get("rf_importance")
stability = data.get("stability")
roc_results = data.get("roc_results")
validation_ranking = data.get("validation_ranking")
validation_stats = data.get("validation_stats")
go_bp = data.get("go_bp")
go_cc = data.get("go_cc")
go_mf = data.get("go_mf")
kegg = data.get("kegg")
# ==================================================
# MAIN HEADER
# ==================================================



# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("🧬 LUAD Biomarker AI")

st.sidebar.caption("Version 2.0")

st.sidebar.divider()

section = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Overview",
        "🧬 Biomarker Explorer",
        "🤖 AI Biomarker Assistant",
        "📊 Differential Expression",
        "📈 ROC / Validation",
        "🤖 Machine Learning",
        "🔬 Stability",
        "🧪 Pathway Analysis",
        "🏆 Integrated Ranking",
        "📥 Downloads",
    ],
)


st.sidebar.divider()

st.sidebar.markdown(
    """
    **Project**

    TCGA-LUAD

    **Disease**

    Lung Adenocarcinoma

    **Analysis**

    RNA-seq + Validation + ML
    """
)


# ==================================================
# HELPER FUNCTIONS
# ==================================================


def metric_value(df, column, default=0):

    if df is None or df.empty:
        return default

    if column not in df.columns:
        return default

    return df[column].max()


# ==================================================
# OVERVIEW
# ==================================================

if section == "🏠 Overview":

    st.title("🧬 LUAD Cancer Biomarker AI Platform")

    st.markdown(
        """
        ### Lung Adenocarcinoma Biomarker Discovery

        An evidence-driven platform integrating differential expression,
        independent validation, ROC/AUC analysis, machine learning,
        biomarker stability, and pathway evidence.
        """
    )

    st.divider()

    n_degs = len(deg) if deg is not None else 0

    n_candidates = (
        len(ranking)
        if ranking is not None
        else 0
    )

    n_top = (
        len(top15)
        if top15 is not None
        else 0
    )

    best_auc = metric_value(
        roc_results,
        "AUC",
        0,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🧬 Significant DEGs",
            f"{n_degs:,}",
        )

    with col2:
        st.metric(
            "🔬 Candidates",
            n_candidates,
        )

    with col3:
        st.metric(
            "🏆 Top Biomarkers",
            n_top,
        )

    with col4:
        st.metric(
            "📈 Best ROC-AUC",
            f"{best_auc:.3f}",
        )

    st.divider()

    st.subheader("🏆 Top Biomarker Candidates")

    if top15 is not None and not top15.empty:

        columns = [
            c
            for c in [
                "gene_name",
                "validation_rank",
                "AUC",
                "stability_score",
                "ML_rank",
                "log2FoldChange",
                "padj",
            ]
            if c in top15.columns
        ]

        st.dataframe(
            top15[columns],
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.warning(
            "Top biomarker data could not be loaded."
        )

    st.divider()

    st.subheader("🔬 Evidence Pipeline")

    st.markdown(
        """
        **Differential Expression**
        → **Candidate Selection**
        → **Independent Validation**
        → **ROC/AUC**
        → **Machine Learning**
        → **Stability**
        → **Integrated Ranking**
        """
    )

# ==================================================
# DIFFERENTIAL EXPRESSION
# ==================================================

elif section == "📊 Differential Expression":

    show_differential_expression(deg)

# ==================================================
# ROC / INDEPENDENT VALIDATION
# ==================================================

elif section == "📈 ROC / Validation":

    show_roc_validation(
        roc_results,
        validation_stats,
        validation_ranking,
    )

elif section == "🤖 Machine Learning":

    show_machine_learning(data)

# ==================================================
# BIOMARKER EXPLORER
# ==================================================

elif section == "🧬 Biomarker Explorer":

    show_biomarker_explorer(data)

elif section == "🤖 AI Biomarker Assistant":

    show_ai_assistant(data)

elif section == "🔎 Evidence Explorer":

    show_evidence_explorer(data)

elif section == "🤖 AI Research Assistant":

    show_ai_assistant(data)


# ==================================================
# DIFFERENTIAL EXPRESSION
# ==================================================

elif section == "📊 Differential Expression":

    st.title("📊 Differential Expression")

    if deg is None or deg.empty:

        st.warning(
            "Differential expression data could not be loaded."
        )

    else:

        st.metric(
            "Significant Differentially Expressed Genes",
            f"{len(deg):,}",
        )

        st.dataframe(
            deg,
            use_container_width=True,
            hide_index=True,
        )


# ==================================================
# ROC / VALIDATION
# ==================================================

elif section == "📈 ROC / Validation":

    st.title("📈 ROC / Validation")

    if roc_results is None or roc_results.empty:

        st.warning(
            "ROC/AUC results could not be loaded."
        )

    else:

        st.subheader("ROC/AUC Results")

        display_columns = [
            c
            for c in [
                "gene_name",
                "AUC",
                "CI_lower",
                "CI_upper",
                "sensitivity",
                "specificity",
                "ROC_rank",
            ]
            if c in roc_results.columns
        ]

        st.dataframe(
            roc_results[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        st.subheader(
            "Independent Validation"
        )

        if validation_stats is not None:

            st.dataframe(
                validation_stats,
                use_container_width=True,
                hide_index=True,
            )


# ==================================================
# MACHINE LEARNING
# ==================================================

elif section == "🤖 Machine Learning":

    st.title("🤖 Machine Learning")

    if model_comparison is not None:

        st.subheader("Model Comparison")

        st.dataframe(
            model_comparison,
            use_container_width=True,
            hide_index=True,
        )

    if rf_importance is not None:

        st.subheader(
            "Random Forest Feature Importance"
        )

        st.dataframe(
            rf_importance,
            use_container_width=True,
            hide_index=True,
        )
elif section == "🔬 Stability":

    show_stability(data)

elif section == "🧪 Pathway Analysis":

    show_pathway_analysis(data)

# ==================================================
# INTEGRATED RANKING
# ==================================================

elif section == "🏆 Integrated Ranking":

    show_integrated_ranking(data)


# ==================================================
# DOWNLOADS
# ==================================================

elif section == "📥 Downloads":

    st.title("📥 Research Data & Downloads")

    st.markdown(
        """
        Download the canonical datasets used by the
        LUAD Cancer Biomarker AI Platform.
        """
    )
    st.subheader("📋 Research Summary")

    st.markdown(
        """
        This section provides the canonical V2 research outputs.
        All datasets are derived from the validated LUAD biomarker
        analysis pipeline and are provided for further analysis,
        reproducibility, and reporting.
        """
    )

    summary_data = {
        "Metric": [
            "Significant DEGs",
            "Biomarker Candidates",
            "Top Biomarkers",
            "Validated Biomarkers",
            "GO Biological Process Terms",
            "GO Cellular Component Terms",
            "GO Molecular Function Terms",
            "KEGG Pathways",
        ],
        "Value": [
            len(deg) if deg is not None else 0,
            len(ranking) if ranking is not None else 0,
            len(top15) if top15 is not None else 0,
            len(validation_stats)
            if validation_stats is not None
            else 0,
            len(go_bp) if go_bp is not None else 0,
            len(go_cc) if go_cc is not None else 0,
            len(go_mf) if go_mf is not None else 0,
            len(kegg) if kegg is not None else 0,
        ],
    }

    summary_df = pd.DataFrame(summary_data)

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="📥 Download Research Summary",
        data=summary_df.to_csv(index=False),
        file_name="LUAD_research_summary.csv",
        mime="text/csv",
    )

    st.divider()

    st.subheader("📦 Canonical Analysis Datasets")

    download_items = {
        "Top Biomarkers": top15,
        "Integrated Ranking": ranking,
        "ROC / AUC Results": roc_results,
        "Validation Statistics": validation_stats,
        "ML Importance": rf_importance,
        "Stability Results": stability,
        "GO Biological Process": go_bp,
        "GO Cellular Component": go_cc,
        "GO Molecular Function": go_mf,
        "KEGG Pathways": kegg,
    }

    for label, dataframe in download_items.items():

        if dataframe is not None and not dataframe.empty:

            st.download_button(
                label=f"📥 Download {label}",
                data=dataframe.to_csv(index=False),
                file_name=(
                    label.lower()
                    .replace(" ", "_")
                    .replace("/", "_")
                    + ".csv"
                ),
                mime="text/csv",
            )


# ==================================================
# FOOTER
# ==================================================

st.sidebar.divider()

st.sidebar.caption(
    "LUAD Cancer Biomarker AI Platform"
)

st.sidebar.caption(
    "Version 2.0"
)
