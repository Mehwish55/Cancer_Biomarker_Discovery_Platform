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
from views.data_upload import show_data_upload

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="OncoNexa — AI-Powered Pan-Cancer Biomarker Discovery Platform",
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

st.sidebar.title("🧬 OncoNexa")

st.sidebar.caption("Version 2.0")

st.sidebar.divider()

section = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Overview",
        "🚀 New Analysis",
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

    OncoNexa

    **Disease**

    Cancer Biomarker Discovery

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

    st.title("🧬 OncoNexa")

    st.markdown(
        """
        ## AI-Powered Cancer Biomarker Discovery

        **From molecular data to evidence-supported biomarker candidates.**

        OncoNexa integrates statistical analysis, machine learning,
        validation, biomarker stability, and functional biology into
        one streamlined research workflow.
        """
    )

    st.divider()

    st.subheader("🚀 What OncoNexa Does")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            ### 🔬 Discover
            Identify and prioritize candidate cancer biomarkers
            from molecular and differential-expression data.
            """
        )

    with col2:
        st.markdown(
            """
            ### 🤖 Validate
            Combine statistical validation, ROC/AUC analysis,
            machine learning, and biomarker stability.
            """
        )

    with col3:
        st.markdown(
            """
            ### 🧬 Interpret
            Connect candidate biomarkers with biological processes,
            pathways, and supporting evidence.
            """
        )

    st.divider()

    st.subheader("⚙️ Integrated Discovery Workflow")

    workflow = [
        ("01", "Data Input", "Molecular / expression data"),
        ("02", "Differential Expression", "Identify significant candidates"),
        ("03", "Candidate Discovery", "Prioritize biomarker candidates"),
        ("04", "Validation", "ROC/AUC and independent evidence"),
        ("05", "Machine Learning", "Feature importance and prediction"),
        ("06", "Stability", "Assess reproducibility across folds"),
        ("07", "Functional Biology", "Pathways and biological interpretation"),
        ("08", "Integrated Ranking", "Generate a prioritized shortlist"),
    ]

    st.markdown(
        """
        <style>
        .workflow-card {
            border: 1px solid rgba(128, 128, 128, 0.35);
            border-radius: 12px;
            padding: 18px;
            min-height: 145px;
            margin-bottom: 18px;
            background: rgba(128, 128, 128, 0.06);
        }

        .workflow-number {
            font-size: 0.85rem;
            font-weight: 700;
            opacity: 0.75;
            margin-bottom: 8px;
        }

        .workflow-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 10px;
            min-height: 48px;
        }

        .workflow-description {
            font-size: 0.88rem;
            line-height: 1.45;
            opacity: 0.8;
        }

        .workflow-arrow {
            text-align: center;
            font-size: 1.4rem;
            opacity: 0.6;
            padding-top: 45px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # First workflow row
    cols = st.columns([1, 0.12, 1, 0.12, 1, 0.12, 1])

    for i, (number, title, description) in enumerate(workflow[:4]):
        card_col = cols[i * 2]

        with card_col:
            st.markdown(
                f"""
                <div class="workflow-card">
                    <div class="workflow-number">{number}</div>
                    <div class="workflow-title">{title}</div>
                    <div class="workflow-description">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if i < 3:
            with cols[i * 2 + 1]:
                st.markdown(
                    '<div class="workflow-arrow">→</div>',
                    unsafe_allow_html=True,
                )

    # Second workflow row
    cols = st.columns([1, 0.12, 1, 0.12, 1, 0.12, 1])

    for i, (number, title, description) in enumerate(workflow[4:]):
        card_col = cols[i * 2]

        with card_col:
            st.markdown(
                f"""
                <div class="workflow-card">
                    <div class="workflow-number">{number}</div>
                    <div class="workflow-title">{title}</div>
                    <div class="workflow-description">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if i < 3:
            with cols[i * 2 + 1]:
                st.markdown(
                    '<div class="workflow-arrow">→</div>',
                    unsafe_allow_html=True,
                )

    st.divider()

    st.subheader("📊 Current Demonstration")

    st.markdown(
        """
        ### Lung Adenocarcinoma — TCGA-LUAD

        The current OncoNexa demonstration uses a validated
        **lung adenocarcinoma (LUAD)** biomarker analysis.

        This represents the first disease-specific implementation
        of the platform. The architecture is designed to support
        expansion to additional cancer types.
        """
    )

    n_degs = len(deg) if deg is not None else 0
    n_candidates = len(ranking) if ranking is not None else 0
    n_top = len(top15) if top15 is not None else 0

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
            "🔬 Candidates Evaluated",
            n_candidates,
        )

    with col3:
        st.metric(
            "🏆 Prioritized Biomarkers",
            n_top,
        )

    with col4:
        st.metric(
            "📈 Best ROC-AUC",
            f"{best_auc:.3f}",
        )

    st.divider()

    st.subheader("🧪 Available Research Modules")

    modules = [
        ("🧬 Biomarker Explorer", "Explore candidate biomarkers and evidence."),
        ("📊 Differential Expression", "Inspect differential-expression results."),
        ("📈 ROC / Validation", "Evaluate diagnostic discrimination."),
        ("🤖 Machine Learning", "Explore ML-based biomarker evidence."),
        ("🔬 Biomarker Stability", "Assess reproducibility across validation folds."),
        ("🧪 Pathway Analysis", "Explore functional and pathway enrichment."),
        ("🏆 Integrated Ranking", "Review combined biomarker prioritization."),
        ("💡 AI Research Assistant", "Interact with the evidence through an AI-assisted interface."),
    ]

    cols = st.columns(2)

    for i, (title, description) in enumerate(modules):
        with cols[i % 2]:
            st.markdown(
                f"""
                **{title}**

                {description}
                """
            )

    st.divider()

    st.info(
        "Current scope: OncoNexa is demonstrated using TCGA-LUAD data. "
        "Additional cancer types can be incorporated as the platform expands."
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
        OncoNexa — AI-Powered Cancer Biomarker Discovery Platform.
        """
    )
    st.subheader("📋 Research Summary")

    st.markdown(
        """
        This section provides the canonical V2 research outputs.
        The current demonstration uses the validated LUAD biomarker
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
    "OncoNexa — AI-Powered Pan-Cancer Biomarker Discovery Platform"
)

st.sidebar.caption(
    "Version 2.0"
)
