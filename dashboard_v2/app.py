import streamlit as st
import pandas as pd

from core.data_loader import load_dataset
from core.customer_report import build_customer_report
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
from views.pricing import show_pricing

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
# GLOBAL ONCONEXA DARK THEME
# ==================================================

st.markdown(
    """
    <style>

    /* ==================================================
       GLOBAL APPLICATION
       ================================================== */

    .stApp,
    .block-container { padding-top: 1.5rem !important; }
        padding-top: 1.5rem !important;
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .main,
    .block-container {
        padding-top: 1.5rem !important;
        background-color: #0B0B0B !important;
        color: #F5F5F5 !important;
    }

    [data-testid="stHeader"] {
        background-color: #0B0B0B !important;
    }

    [data-testid="stToolbar"] {
        background-color: #0B0B0B !important;
    }

    /* ==================================================
       SIDEBAR
       ================================================== */

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div:first-child,
    [data-testid="stSidebarNav"] {
        background-color: #111111 !important;
    }

    [data-testid="stSidebar"] * {
        color: #F5F5F5 !important;
    }

    /* ==================================================
       TEXT
       ================================================== */

    body,
    p,
    span,
    label,
    div {
        color: #F5F5F5;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }

    a {
        color: #8AB4F8 !important;
    }

    /* ==================================================
       METRICS
       ================================================== */

    [data-testid="stMetric"] {
        background-color: #151515 !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }

    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }

    [data-testid="stMetricLabel"] {
        color: #D1D5DB !important;
    }

    [data-testid="stMetricDelta"] {
        color: #D1D5DB !important;
    }

    /* ==================================================
       DATAFRAMES / TABLES
       ================================================== */

    [data-testid="stDataFrame"],
    [data-testid="stDataEditor"] {
        background-color: #151515 !important;
        color: #F5F5F5 !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 8px !important;
    }

    [data-testid="stDataFrame"] > div,
    [data-testid="stDataEditor"] > div {
        background-color: #151515 !important;
    }

    [data-testid="stDataFrame"] iframe {
        background-color: #151515 !important;
    }

    /* ==================================================
       INPUTS
       ================================================== */

    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: #181818 !important;
        color: #F5F5F5 !important;
        border: 1px solid #333333 !important;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stNumberInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #888888 !important;
    }

    /* ==================================================
       SELECTBOX / MULTISELECT
       ================================================== */

    [data-testid="stSelectbox"] > div,
    [data-testid="stMultiSelect"] > div {
        background-color: #181818 !important;
        color: #F5F5F5 !important;
    }

    [data-baseweb="select"] > div {
        background-color: #181818 !important;
        color: #F5F5F5 !important;
        border-color: #333333 !important;
    }

    [data-baseweb="select"] input {
        color: #F5F5F5 !important;
    }

    [data-baseweb="popover"] {
        background-color: #181818 !important;
        color: #F5F5F5 !important;
    }

    [role="option"] {
        background-color: #181818 !important;
        color: #F5F5F5 !important;
    }

    [role="option"]:hover {
        background-color: #252525 !important;
    }

    /* ==================================================
       FILE UPLOADER
       ================================================== */

    [data-testid="stFileUploader"] {
        background-color: #151515 !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 10px !important;
    }

    [data-testid="stFileUploader"] * {
        color: #F5F5F5 !important;
    }

    /* ==================================================
       BUTTONS
       ================================================== */

    button {
        color: #F5F5F5 !important;
        background-color: #181818 !important;
        border-color: #333333 !important;
    }

    button:hover {
        background-color: #252525 !important;
        border-color: #555555 !important;
    }

    /* ==================================================
       EXPANDERS
       ================================================== */

    [data-testid="stExpander"] {
        background-color: #151515 !important;
        border: 1px solid #2A2A2A !important;
        border-radius: 8px !important;
    }

    [data-testid="stExpander"] * {
        color: #F5F5F5 !important;
    }

    /* ==================================================
       TABS
       ================================================== */

    [data-baseweb="tab-list"] {
        background-color: #0B0B0B !important;
    }

    [data-baseweb="tab"] {
        color: #D1D5DB !important;
        background-color: #0B0B0B !important;
    }

    [aria-selected="true"] {
        color: #FFFFFF !important;
    }

    /* ==================================================
       ALERTS / STATUS BOXES
       ================================================== */

    [data-testid="stAlert"] {
        background-color: #151515 !important;
        color: #F5F5F5 !important;
        border: 1px solid #2A2A2A !important;
    }

    /* ==================================================
       CODE BLOCKS
       ================================================== */

    [data-testid="stCodeBlock"] {
        background-color: #151515 !important;
        border: 1px solid #2A2A2A !important;
    }

    /* ==================================================
       DIVIDERS
       ================================================== */

    hr {
        border-color: #2A2A2A !important;
    }

    /* ==================================================
       WORKFLOW / CUSTOM CARDS
       ================================================== */

    .workflow-card {
        background-color: #151515 !important;
        border: 1px solid #2A2A2A !important;
        color: #F5F5F5 !important;
    }

    .workflow-number,
    .workflow-title,
    .workflow-description,
    .workflow-arrow {
        color: #F5F5F5 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
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
# NAVIGATION STATE
# ==================================================

if "navigation_request" not in st.session_state:
    st.session_state["navigation_request"] = None

if "nav_radio" not in st.session_state:
    st.session_state["nav_radio"] = "🏠 Overview"

if st.session_state["navigation_request"] is not None:
    st.session_state["nav_radio"] = st.session_state["navigation_request"]
    st.session_state["navigation_request"] = None


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.title("🧬 OncoNexa")


st.sidebar.divider()

section = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Overview",
        "🚀 New Analysis",
        "📊 Differential Expression",
        "🧬 Biomarker Explorer",
        "📈 ROC / Validation",
        "🧠 Machine Learning",
        "🔬 Stability",
        "🧪 Pathway Analysis",
        "🏆 Integrated Ranking",
        "🔎 Evidence Explorer",
        "💡 AI Biomarker Assistant",
        "📥 Downloads",
        "💼 Pricing & Services",
    ],
    key="nav_radio",
)


st.sidebar.divider()

st.sidebar.markdown(
    """
    **PROJECT**  
    OncoNexa

    **DISEASE**  
    Cancer Biomarker Discovery

    **ANALYSIS**  
    RNA-seq · Validation · ML
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

if section == "🚀 New Analysis":

    from views.data_upload import show_data_upload

    st.title("🚀 New Analysis")

    st.info(
        "🧪 Testing mode: this professional analysis workflow is "
        "temporarily open for platform testing."
    )

    show_data_upload()

elif section == "🏠 Overview":

    # ==================================================
    # ONCONEXA LANDING PAGE
    # ==================================================

    st.markdown(
        """
        <style>
        .onco-hero {
            padding: 28px 0 18px 0;
        }

        .onco-eyebrow {
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            opacity: 1;
            color: #ffffff;
            margin-bottom: 10px;
        }

        .onco-hero-title {
            font-size: 2.35rem;
            font-weight: 800;
            line-height: 1.12;
            margin-bottom: 14px;
        }

        .onco-hero-text {
            font-size: 0.92rem;
            line-height: 1.5;
            max-width: 850px;
            color: #d0d0d0;
            opacity: 1;
            margin-bottom: 8px;
        }

        .onco-feature-card {
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-radius: 14px;
            padding: 20px;
            min-height: 155px;
            background: rgba(128, 128, 128, 0.055);
        }

        .onco-feature-icon {
            font-size: 1.45rem;
            margin-bottom: 8px;
        }

        .onco-feature-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 8px;
        }

        .onco-feature-text {
            font-size: 0.92rem;
            line-height: 1.5;
            color: #d0d0d0;
            opacity: 1;
        }

        .onco-section-label {
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 1;
            color: #ffffff;
            margin-bottom: 5px;
        }

        div.stButton:has(button[kind="secondary"]) button {
            border: 1px solid #1976d2;
            background-color: #1976d2;
            color: white;
            font-weight: 700;
        }

        div.stButton:has(button[kind="secondary"]) button:hover {
            border-color: #1565c0;
            background-color: #1565c0;
            color: white;
        }

        .onco-cta {
            border: 1px solid rgba(128, 128, 128, 0.3);
            border-radius: 16px;
            padding: 26px;
            margin-top: 10px;
            background: rgba(128, 128, 128, 0.055);
        }

        .onco-cta-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 8px;
        }

        .onco-cta-text {
            font-size: 0.92rem;
            line-height: 1.5;
            color: #d0d0d0;
            opacity: 1;
        }

        .module-card {
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 12px;
            padding: 17px;
            min-height: 105px;
            background: rgba(128, 128, 128, 0.045);
        }

        .module-title {
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 7px;
        }

        .module-description {
            font-size: 0.92rem;
            line-height: 1.5;
            color: #d0d0d0;
            opacity: 1;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # BLUE FRONT-PAGE CTA BUTTONS
    # --------------------------------------------------

    st.markdown(
        """
        <style>
        div[data-testid="stButton"] button {
            background-color: #2563eb !important;
            color: white !important;
            border: 1px solid #2563eb !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
        }

        div[data-testid="stButton"] button:hover {
            background-color: #1d4ed8 !important;
            border-color: #1d4ed8 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # HERO
    # --------------------------------------------------

    st.markdown(
        """<div class="onco-hero">
<div class="onco-eyebrow">🧬 OncoNexa</div>
<div class="onco-hero-title">AI-Powered Pan-Cancer<br>Biomarker Discovery</div>
<div class="onco-hero-text">From molecular data to evidence-supported biomarker candidates. OncoNexa integrates statistical analysis, machine learning, validation, stability assessment, and biological interpretation into one streamlined research workflow.</div>
</div>""",
        unsafe_allow_html=True,
    )

    cta1, cta2 = st.columns([1, 1])

    with cta1:
        if st.button(
            "🚀 Start a New Analysis",
            use_container_width=True,
            key="overview_new_analysis",
        ):
            st.session_state["navigation_request"] = "🚀 New Analysis"
            st.rerun()

    with cta2:
        if st.button(
            "📊 Explore Reference Analysis",
            use_container_width=True,
            key="overview_reference_analysis",
        ):
            st.session_state["navigation_request"] = "🏠 Overview"
            st.rerun()

    st.divider()

    # --------------------------------------------------
    # CORE CAPABILITIES
    # --------------------------------------------------

    st.markdown(
        '<div class="onco-section-label">CORE CAPABILITIES</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### From discovery to biological interpretation"
    )

    features = [
        (
            "🔬",
            "Discover",
            "Identify candidate biomarkers from molecular and "
            "differential-expression data.",
        ),
        (
            "🤖",
            "Validate",
            "Combine ROC/AUC analysis, machine learning, "
            "and biomarker stability assessment.",
        ),
        (
            "🧬",
            "Interpret",
            "Connect candidate biomarkers with pathways, "
            "functional biology, and supporting evidence.",
        ),
        (
            "🏆",
            "Prioritize",
            "Integrate multiple evidence layers into a "
            "structured biomarker shortlist.",
        ),
    ]

    cols = st.columns(4)

    for col, (icon, title, description) in zip(cols, features):
        with col:
            st.markdown(
                f"""
                <div class="onco-feature-card">
                    <div class="onco-feature-icon">{icon}</div>
                    <div class="onco-feature-title">{title}</div>
                    <div class="onco-feature-text">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # --------------------------------------------------
    # WORKFLOW
    # --------------------------------------------------

    st.markdown(
        '<div class="onco-section-label">INTEGRATED WORKFLOW</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### A structured path from data to candidate biomarkers"
    )

    workflow = [
        ("01", "Data Input", "Molecular / expression data"),
        ("02", "Differential Expression", "Identify significant candidates"),
        ("03", "Candidate Discovery", "Explore biomarker candidates"),
        ("04", "Validation", "ROC/AUC and validation evidence"),
        ("05", "Machine Learning", "Feature importance and prediction"),
        ("06", "Stability", "Assess reproducibility across folds"),
        ("07", "Functional Biology", "Pathways and biological interpretation"),
        ("08", "Integrated Ranking", "Generate a prioritized shortlist"),
    ]

    cols = st.columns(4)

    for i, (number, title, description) in enumerate(workflow):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="onco-feature-card">
                    <div class="workflow-number">{number}</div>
                    <div class="onco-feature-title">{title}</div>
                    <div class="onco-feature-text">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # --------------------------------------------------
    # PLATFORM MODULES
    # --------------------------------------------------

    st.markdown(
        '<div class="onco-section-label">PLATFORM MODULES</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Explore the research workflow")

    modules = [
        ("🧬 Biomarker Explorer", "Explore candidate biomarkers and evidence."),
        ("📊 Differential Expression", "Inspect differential-expression results."),
        ("📈 ROC / Validation", "Evaluate diagnostic discrimination."),
        ("🧠 Machine Learning", "Explore ML-based biomarker evidence."),
        ("🔬 Biomarker Stability", "Assess reproducibility across validation folds."),
        ("🧪 Pathway Analysis", "Explore functional and pathway enrichment."),
        ("🏆 Integrated Ranking", "Review combined biomarker prioritization."),
        ("💡 AI Research Assistant", "Interact with biomarker evidence through an AI-assisted interface."),
    ]

    cols = st.columns(2)

    for i, (title, description) in enumerate(modules):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="module-card">
                    <div class="module-title">{title}</div>
                    <div class="module-description">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # --------------------------------------------------
    # REFERENCE ANALYSIS
    # --------------------------------------------------

    st.markdown(
        '<div class="onco-section-label">REFERENCE ANALYSIS</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Explore a completed biomarker discovery analysis")

    st.markdown(
        """
        Explore a validated reference analysis and see how OncoNexa
        connects differential expression, biomarker validation,
        machine learning, stability, pathway analysis, and integrated
        prioritization.
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
        st.metric("🧬 Significant DEGs", f"{n_degs:,}")

    with col2:
        st.metric("🔬 Candidates Evaluated", n_candidates)

    with col3:
        st.metric("🏆 Prioritized Biomarkers", n_top)

    with col4:
        st.metric("📈 Best ROC-AUC", f"{best_auc:.3f}")

    st.divider()

    # --------------------------------------------------
    # CUSTOMER CTA
    # --------------------------------------------------

    st.markdown(
        """<div class="onco-cta">
<div class="onco-cta-title">Ready to analyze your own cancer dataset?</div>
<div class="onco-cta-text">Upload your expression matrix and sample metadata to run a customer-specific biomarker discovery workflow through OncoNexa.</div>
</div>""",
        unsafe_allow_html=True,
    )

    if st.button(
        "🚀 Start a New Analysis",
        use_container_width=True,
        key="overview_new_analysis_bottom",
    ):
        st.session_state["navigation_request"] = "🚀 New Analysis"
        st.rerun()

    st.caption(
        "A validated reference analysis is available for platform exploration."
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

elif section == "🧠 Machine Learning":

    show_machine_learning(data)

# ==================================================
# BIOMARKER EXPLORER
# ==================================================

elif section == "🧬 Biomarker Explorer":

    show_biomarker_explorer(data)

elif section == "💡 AI Biomarker Assistant":

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

elif section == "🧠 Machine Learning":

    st.title("🧠 Machine Learning")

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

    st.title("📥 OncoNexa Reports & Downloads")

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    if customer_context is None:

        st.info(
            "Upload your dataset and complete an analysis "
            "to generate the OncoNexa report and downloadable results."
        )

    else:

        cancer_type = (
            getattr(customer_context, "cancer_type", None)
            or "Uploaded Dataset"
        )

        comparison = (
            getattr(customer_context, "comparison", None)
            or "Group comparison"
        )

        analysis_id = (
            getattr(customer_context, "analysis_id", None)
            or "customer_analysis"
        )

        st.markdown(
            f"""
            ### OncoNexa Analysis Report

            **Cancer / Dataset:** {cancer_type}  
            **Comparison:** {comparison}  
            **Analysis ID:** `{analysis_id}`
            """
        )

        st.divider()

        # ==================================================
        # PROFESSIONAL PDF REPORT
        # ==================================================

        st.subheader("📄 Professional OncoNexa Report")

        st.markdown(
            """
            Generate a professional PDF containing
            the key findings from your OncoNexa biomarker analysis.
            """
        )

        try:

            pdf_bytes = build_customer_report(
                customer_context=customer_context,
                roc_results=st.session_state.get(
                    "onconexa_customer_roc_results"
                ),
                ml_results=st.session_state.get(
                    "onconexa_customer_ml_results"
                ),
                stability_results=st.session_state.get(
                    "onconexa_customer_stability_results"
                ),
                pathway_cache=st.session_state.get(
                    "onconexa_customer_pathway_cache"
                ),
            )

            st.download_button(
                label="📄 Download Professional OncoNexa Report",
                data=pdf_bytes,
                file_name=f"OncoNexa_Biomarker_Report_{analysis_id}.pdf",
                mime="application/pdf",
                type="primary",
            )

            st.caption(
                "Includes differential expression, biomarker discrimination, "
                "machine learning, stability, functional biology, interpretation, "
                "and next-step recommendations where available."
            )

        except Exception as exc:

            st.error(
                f"Unable to generate the PDF report: {exc}"
            )

        st.divider()

        # ==================================================
        # CUSTOMER DATA DOWNLOADS
        # ==================================================

        st.subheader("📦 Analysis Results")

        expression_data = getattr(
            customer_context,
            "expression_data",
            None,
        )

        metadata = getattr(
            customer_context,
            "metadata",
            None,
        )

        differential_expression = getattr(
            customer_context,
            "differential_expression",
            None,
        )

        download_items = [
            (
                "Differential Expression Results",
                differential_expression,
                "differential_expression.csv",
            ),
            (
                "Expression Matrix",
                expression_data,
                "expression_matrix.csv",
            ),
            (
                "Sample Metadata",
                metadata,
                "sample_metadata.csv",
            ),
            (
                "ROC / AUC Results",
                st.session_state.get(
                    "onconexa_customer_roc_results"
                ),
                "roc_auc_results.csv",
            ),
            (
                "Machine Learning Results",
                st.session_state.get(
                    "onconexa_customer_ml_results"
                ),
                "machine_learning_results.csv",
            ),
            (
                "Stability Results",
                st.session_state.get(
                    "onconexa_customer_stability_results"
                ),
                "stability_results.csv",
            ),
        ]

        available_downloads = 0

        for label, dataframe, filename in download_items:

            if dataframe is not None:

                try:

                    if hasattr(dataframe, "empty") and dataframe.empty:
                        continue

                    csv_data = dataframe.to_csv(index=False)

                    st.download_button(
                        label=f"📥 Download {label}",
                        data=csv_data,
                        file_name=filename,
                        mime="text/csv",
                        key=f"download_{filename}",
                    )

                    available_downloads += 1

                except Exception:
                    continue

        if available_downloads == 0:

            st.info(
                "No downloadable analysis result tables are currently available."
            )


# ==================================================
# PRICING & SERVICES
# ==================================================

elif section == "💼 Pricing & Services":

    show_pricing()


# ==================================================
# FOOTER
# ==================================================

st.sidebar.divider()

st.sidebar.markdown(
    "**OncoNexa**"
)

st.sidebar.caption(
    "AI-Powered Pan-Cancer Biomarker Discovery Platform"
)


