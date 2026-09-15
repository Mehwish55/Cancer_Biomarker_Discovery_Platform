import streamlit as st

from core.evidence_engine import get_biomarker_evidence
from core.customer_evidence import (
    get_customer_biomarker_evidence,
    evidence_exists,
)
from core.customer_ranking import calculate_customer_integrated_ranking


def _safe_float(value, decimals=3):
    """Safely format numeric values."""
    try:
        if value is None:
            return "N/A"
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def _safe_int(value):
    """Safely format integer values."""
    try:
        if value is None:
            return "N/A"
        return str(int(value))
    except (TypeError, ValueError):
        return "N/A"




def _show_customer_evidence(customer_context):
    """Display evidence for the active customer analysis."""

    st.title("🧬 Biomarker Evidence Explorer")

    st.markdown(
        """
        Explore the evidence supporting biomarkers identified from
        your uploaded cancer expression dataset.

        The evidence shown here is retrieved directly from the
        current analysis pipeline.
        """
    )

    st.divider()

    differential_expression = (
        customer_context.differential_expression
    )

    # Recover the already-computed customer DE results from session state
    # if the central context does not currently contain them.
    if (
        differential_expression is None
        or differential_expression.empty
    ):
        cached_de = st.session_state.get(
            "onconexa_analysis_results"
        )

        if cached_de is not None:
            differential_expression = cached_de

    # Standardize the DE gene identifier for the Evidence Explorer.
    # The generic DE engine outputs this column as "gene".
    if (
        differential_expression is not None
        and not differential_expression.empty
        and "gene_name" not in differential_expression.columns
        and "gene" in differential_expression.columns
    ):
        differential_expression = differential_expression.rename(
            columns={"gene": "gene_name"}
        )

    if (
        differential_expression is None
        or differential_expression.empty
        or "gene_name" not in differential_expression.columns
    ):
        st.warning(
            "No differential-expression results are available."
        )
        return

    # --------------------------------------------------
    # Retrieve customer analysis caches
    # --------------------------------------------------

    roc_results = st.session_state.get(
        "onconexa_customer_roc_results"
    )

    roc_analysis_id = st.session_state.get(
        "onconexa_customer_roc_analysis_id"
    )

    if (
        roc_results is None
        or roc_analysis_id != customer_context.analysis_id
    ):
        roc_results = None

    ml_results = st.session_state.get(
        "onconexa_customer_ml_results"
    )

    ml_analysis_id = st.session_state.get(
        "onconexa_customer_ml_analysis_id"
    )

    if (
        ml_results is None
        or ml_analysis_id != customer_context.analysis_id
    ):
        ml_results = None

    stability_results = st.session_state.get(
        "onconexa_customer_stability_results"
    )

    stability_analysis_id = st.session_state.get(
        "onconexa_customer_stability_analysis_id"
    )

    if (
        stability_results is None
        or stability_analysis_id != customer_context.analysis_id
    ):
        stability_results = None

    pathway_cache = st.session_state.get(
        "onconexa_customer_pathway_cache"
    )

    pathway_results = None

    if isinstance(pathway_cache, dict):
        if (
            pathway_cache.get("analysis_id")
            == customer_context.analysis_id
        ):
            pathway_results = pathway_cache.get("result")

    # --------------------------------------------------
    # Calculate the same integrated ranking used by the
    # customer Integrated Ranking page.
    # --------------------------------------------------

    integrated_ranking = None

    try:
        integrated_ranking = calculate_customer_integrated_ranking(
            differential_expression=differential_expression,
            roc_results=roc_results,
            ml_results=ml_results,
            stability_results=stability_results,
            pathway_results=pathway_results,
        )
    except Exception as exc:
        st.warning(
            f"Integrated ranking evidence is temporarily unavailable: {exc}"
        )

    # --------------------------------------------------
    # Build gene list from customer ranking / DE
    # --------------------------------------------------

    genes = []

    if (
        integrated_ranking is not None
        and not integrated_ranking.empty
        and "gene_name" in integrated_ranking.columns
    ):
        genes = (
            integrated_ranking["gene_name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    if not genes:
        genes = (
            differential_expression["gene_name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    if not genes:
        st.error("No biomarker candidates are available.")
        return

    selected_gene = st.selectbox(
        "Select biomarker",
        genes,
        index=0,
        key="onconexa_customer_evidence_gene",
    )

    # --------------------------------------------------
    # Collect evidence
    # --------------------------------------------------

    evidence = get_customer_biomarker_evidence(
        gene_name=selected_gene,
        differential_expression=differential_expression,
        roc_results=roc_results,
        ml_results=ml_results,
        stability_results=stability_results,
        pathway_results=pathway_results,
        integrated_ranking=integrated_ranking,
    )

    if not evidence_exists(evidence):
        st.warning(
            f"No supporting evidence could be retrieved for "
            f"{selected_gene}."
        )
        return

    st.header(f"🔬 {selected_gene}")

    st.caption(
        f"Analysis ID: {customer_context.analysis_id}"
    )

    # --------------------------------------------------
    # Integrated evidence
    # --------------------------------------------------

    integrated = evidence.get(
        "integrated_ranking",
        {},
    )

    if integrated:
        st.subheader("🏆 Integrated Evidence")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Integrated Score",
                _safe_float(
                    integrated.get("integrated_score")
                ),
            )

        with col2:
            st.metric(
                "Integrated Rank",
                _safe_int(
                    integrated.get("integrated_rank")
                ),
            )

        with col3:
            st.metric(
                "ROC-AUC",
                _safe_float(
                    integrated.get("AUC")
                ),
            )

        score_columns = [
            ("DE", "score_DE"),
            ("ROC", "score_ROC"),
            ("ML", "score_ML"),
            ("Stability", "score_stability"),
            ("Pathway", "score_pathway"),
        ]

        score_rows = []

        for label, column in score_columns:
            value = integrated.get(column)

            if value is not None:
                score_rows.append(
                    {
                        "Evidence layer": label,
                        "Score": float(value),
                    }
                )

        if score_rows:
            st.dataframe(
                score_rows,
                use_container_width=True,
                hide_index=True,
            )

    # --------------------------------------------------
    # Differential expression
    # --------------------------------------------------

    de = evidence.get(
        "differential_expression",
        {},
    )

    if de:
        st.subheader("🧬 Differential Expression")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "log₂ Fold Change",
                _safe_float(
                    de.get("log2FoldChange")
                ),
            )

        with col2:
            st.metric(
                "Adjusted p-value",
                _safe_float(
                    de.get("padj"),
                    4,
                ),
            )

        with col3:
            st.metric(
                "Base Mean",
                _safe_float(
                    de.get("baseMean"),
                    1,
                ),
            )

        with col4:
            st.metric(
                "Direction",
                str(
                    de.get(
                        "direction",
                        "N/A",
                    )
                ),
            )

    # --------------------------------------------------
    # ROC
    # --------------------------------------------------

    roc = evidence.get(
        "roc_validation",
        {},
    )

    if roc:
        st.subheader("📈 ROC / Diagnostic Performance")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "ROC-AUC",
                _safe_float(
                    roc.get("AUC")
                ),
            )

        with col2:
            st.metric(
                "Sensitivity",
                _safe_float(
                    roc.get("sensitivity")
                ),
            )

        with col3:
            st.metric(
                "Specificity",
                _safe_float(
                    roc.get("specificity")
                ),
            )

        direction = roc.get("direction")

        if direction:
            st.caption(
                f"Classification direction: {direction}"
            )

    # --------------------------------------------------
    # Machine learning
    # --------------------------------------------------

    ml = evidence.get(
        "machine_learning",
        {},
    )

    if ml:
        st.subheader("🤖 Machine Learning Evidence")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "RF Feature Importance",
                _safe_float(
                    ml.get("importance")
                ),
            )

        with col2:
            st.metric(
                "ML Rank",
                _safe_int(
                    ml.get("ML_rank")
                ),
            )

    # --------------------------------------------------
    # Stability
    # --------------------------------------------------

    stability = evidence.get(
        "stability",
        {},
    )

    if stability:
        st.subheader("🔬 Biomarker Stability")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Stability Score",
                _safe_float(
                    stability.get("stability_score"),
                    4,
                ),
            )

        with col2:
            st.metric(
                "Stability Rank",
                _safe_int(
                    stability.get("stability_rank")
                ),
            )

        with col3:
            value = stability.get("top10_stability")

            st.metric(
                "Top-10 Stability",
                f"{float(value) * 100:.0f}%"
                if value is not None
                else "N/A",
            )

        with col4:
            value = stability.get("top20_stability")

            st.metric(
                "Top-20 Stability",
                f"{float(value) * 100:.0f}%"
                if value is not None
                else "N/A",
            )

    # --------------------------------------------------
    # Functional biology
    # --------------------------------------------------

    pathway = evidence.get(
        "pathway",
        [],
    )

    if pathway:
        st.subheader("🧬 Functional Biology / Pathway Evidence")

        pathway_table = []

        for item in pathway:
            pathway_table.append(
                {
                    "Ontology": item.get("ontology"),
                    "GO ID": item.get("GOID"),
                    "Term": item.get("TERM"),
                    "Hits": item.get("Hits"),
                    "Fold Enrichment": item.get(
                        "FoldEnrichment"
                    ),
                    "Adjusted p-value": item.get(
                        "padj"
                    ),
                }
            )

        st.dataframe(
            pathway_table,
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------
    # Evidence availability
    # --------------------------------------------------

    st.divider()

    st.subheader("🔎 Evidence Availability")

    available = []

    for key, label in [
        ("integrated_ranking", "Integrated Ranking"),
        ("differential_expression", "Differential Expression"),
        ("roc_validation", "ROC / Validation"),
        ("machine_learning", "Machine Learning"),
        ("stability", "Stability"),
        ("pathway", "Functional Biology"),
    ]:
        value = evidence.get(key)

        if value:
            available.append(label)

    if available:
        st.success(
            f"Evidence available across {len(available)} "
            f"analysis layers."
        )

        st.write(
            " • ".join(available)
        )
    else:
        st.warning(
            "No supporting evidence layers were found."
        )

    st.caption(
        "Data provenance: current analysis outputs • "
        "OncoNexa evidence presentation layer"
    )


def show_evidence_explorer(data):
    """
    Display evidence-based biomarker profile.

    Uses the active customer analysis when available.
    Otherwise, falls back to the existing static/LUAD evidence layer.
    """

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    st.sidebar.write(
        "DEBUG analysis results:",
        "onconexa_analysis_results" in st.session_state,
    )

    if (
        customer_context is not None
        and customer_context.has_differential_expression()
    ):
        _show_customer_evidence(customer_context)
        return

    st.title("🧬 Biomarker Evidence Explorer")

    st.markdown(
        """
        Explore the evidence supporting each biomarker candidate.

        **Important:** All numerical evidence shown here comes from the
        existing V1 pipeline outputs. V2 does not create a competing
        biological score.
        """
    )

    st.divider()

    ranking = data.get("integrated_ranking")
    top15 = data.get("top15")

    # --------------------------------------------------
    # Determine available genes
    # --------------------------------------------------

    genes = []

    if ranking is not None and not ranking.empty:
        if "gene_name" in ranking.columns:
            genes = (
                ranking["gene_name"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

    elif top15 is not None and not top15.empty:
        if "gene_name" in top15.columns:
            genes = (
                top15["gene_name"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

    if not genes:
        st.error("No biomarker genes are available.")
        return

    # --------------------------------------------------
    # Gene selector
    # --------------------------------------------------

    selected_gene = st.selectbox(
        "Select biomarker",
        genes,
        index=0,
    )

    # --------------------------------------------------
    # Retrieve grounded evidence
    # --------------------------------------------------

    evidence = get_biomarker_evidence(
        data,
        selected_gene,
    )

    if not evidence:
        st.warning(
            f"No evidence could be retrieved for {selected_gene}."
        )
        return

    # --------------------------------------------------
    # Header
    # --------------------------------------------------

    st.header(f"🔬 {selected_gene}")

    st.caption(
        "Evidence retrieved from canonical V1 pipeline outputs."
    )

    # --------------------------------------------------
    # Integrated ranking
    # --------------------------------------------------

    integrated = evidence.get(
        "integrated_ranking",
        {},
    )

    if integrated:
        st.subheader("🏆 Integrated Evidence")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Official Integrated Score",
                _safe_float(
                    integrated.get("integrated_score")
                ),
            )

        with col2:
            st.metric(
                "Integrated Rank",
                _safe_int(
                    integrated.get("integrated_rank")
                ),
            )

        with col3:
            st.metric(
                "AUC",
                _safe_float(
                    integrated.get("score_AUC")
                ),
            )

        st.info(
            "The Integrated Score and Rank shown above are "
            "the official values generated by the V1 pipeline."
        )

    st.divider()

    # --------------------------------------------------
    # ROC / Validation
    # --------------------------------------------------

    roc = evidence.get(
        "roc_validation",
        {},
    )

    if roc:
        st.subheader("📈 ROC / Diagnostic Performance")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "ROC-AUC",
                _safe_float(
                    roc.get("AUC")
                ),
            )

        with col2:
            st.metric(
                "Sensitivity",
                _safe_float(
                    roc.get("sensitivity")
                ),
            )

        with col3:
            st.metric(
                "Specificity",
                _safe_float(
                    roc.get("specificity")
                ),
            )

    # --------------------------------------------------
    # Independent validation
    # --------------------------------------------------

    validation = evidence.get(
        "independent_validation",
        {},
    )

    if validation:
        st.subheader("🧪 Independent Validation")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Direction",
                str(
                    validation.get(
                        "direction",
                        "N/A",
                    )
                ),
            )

        with col2:
            status = validation.get(
                "validation_status"
            )

            if status is not None:
                st.metric(
                    "Validation Status",
                    str(status),
                )

    # --------------------------------------------------
    # Machine learning
    # --------------------------------------------------

    ml = evidence.get(
        "machine_learning",
        {},
    )

    if ml:
        st.subheader("🤖 Machine Learning Evidence")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Feature Importance",
                _safe_float(
                    ml.get("importance")
                ),
            )

        with col2:
            st.metric(
                "ML Rank",
                _safe_int(
                    ml.get("ML_rank")
                ),
            )
    # --------------------------------------------------
    # Stability
    # --------------------------------------------------

    stability = evidence.get(
        "stability",
        {},
    )

    if stability:
        st.subheader("🔬 Biomarker Stability")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Stability Score",
                _safe_float(
                    stability.get("stability_score"),
                    4,
                ),
            )

        with col2:
            st.metric(
                "Stability Rank",
                _safe_int(
                    stability.get("stability_rank")
                ),
            )

        with col3:
            top10 = stability.get("top10_stability")

            st.metric(
                "Top-10 Stability",
                f"{float(top10) * 100:.0f}%"
                if top10 is not None
                else "N/A",
            )

        with col4:
            top20 = stability.get("top20_stability")

            st.metric(
                "Top-20 Stability",
                f"{float(top20) * 100:.0f}%"
                if top20 is not None
                else "N/A",
            )
    # --------------------------------------------------
    # Differential expression
    # --------------------------------------------------

    de = evidence.get(
        "differential_expression",
        {},
    )

    if de:
        st.subheader("🧬 Differential Expression")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "log₂ Fold Change",
                _safe_float(
                    de.get("log2FoldChange")
                ),
            )

        with col2:
            st.metric(
                "Adjusted p-value",
                _safe_float(
                    de.get("padj"),
                    4,
                ),
            )

        with col3:
            st.metric(
                "Base Mean",
                _safe_float(
                    de.get("baseMean"),
                    1,
                ),
            )

    # --------------------------------------------------
    # Evidence availability
    # --------------------------------------------------

    st.divider()

    st.subheader("🔎 Evidence Availability")

    available = []

    for key, label in [
        ("integrated_ranking", "Integrated Ranking"),
        ("top15", "Top Biomarkers"),
        ("roc_validation", "ROC / Validation"),
        ("independent_validation", "Independent Validation"),
        ("machine_learning", "Machine Learning"),
        ("stability", "Stability"),
        ("differential_expression", "Differential Expression"),
    ]:
        if evidence.get(key):
            available.append(label)

    if available:
        st.success(
            f"Evidence available across {len(available)} "
            f"analysis layers."
        )

        st.write(
            " • ".join(available)
        )

    else:
        st.warning(
            "No supporting evidence layers were found."
        )

    st.caption(
        "Data provenance: canonical V1 analysis outputs • "
        "V2 presentation and interpretation layer"
    )
