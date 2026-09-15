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

    st.title("🔒 Professional Analysis")

    st.markdown(
        """
        ## Analyze Your Cancer Dataset

        Uploading and analyzing your own research dataset is available
        through the OncoNexa professional analysis services.

        ### Research Analysis Services

        **Essential — €200**
        Initial biomarker discovery and biological analysis.

        **Advanced — €500**
        Complete biomarker discovery, validation, machine learning,
        stability analysis, evidence integration, and professional reporting.

        **Custom Research — from €1,000**
        Complex datasets, multiple comparisons, custom workflows,
        additional validation, and customized reporting.
        """
    )

    st.divider()

    st.info(
        "Please request an analysis before uploading your research dataset. "
        "The professional analysis workflow is provided as a paid service."
    )

    st.markdown(
        """
        ### What happens next?

        1. Select the analysis package that matches your project.
        2. Contact OncoNexa to discuss your dataset and requirements.
        3. After the project is confirmed, your dataset can be analyzed
           using the OncoNexa workflow.
        4. You receive the analysis results, tables, figures, and report.
        """
    )

elif section == "🏠 Overview":

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
        /* OncoNexa dark theme */
        .stApp {
            background-color: #0B0B0B;
            color: #F5F5F5;
        }

        [data-testid="stSidebar"] {
            background-color: #050505;
        }

        [data-testid="stHeader"] {
            background-color: #0B0B0B;
        }

        [data-testid="stToolbar"] {
            background-color: #0B0B0B;
        }

        .main {
            background-color: #0B0B0B;
        }

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

    st.subheader("📊 OncoNexa Demonstration")

    st.markdown(
        """
        ### Lung Adenocarcinoma — TCGA-LUAD

        Explore a completed OncoNexa biomarker discovery analysis
        using a validated **lung adenocarcinoma (LUAD)** dataset.

        This free demonstration lets visitors explore the platform's
        biomarker discovery, validation, machine-learning, stability,
        and biological interpretation capabilities.

        **Ready to analyze your own data?** Use **🚀 New Analysis**
        in the sidebar to upload your expression matrix and sample
        metadata for an analysis.
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
        ("🧠 Machine Learning", "Explore ML-based biomarker evidence."),
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
        "Free demonstration: TCGA-LUAD. "
        "Analyses can be performed using uploaded cancer expression "
        "data and sample metadata."
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


