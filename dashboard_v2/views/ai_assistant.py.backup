import streamlit as st

from core.evidence_engine import get_biomarker_evidence
from core.ai_grounding import build_grounded_context


def _fmt(value, digits=3):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def generate_grounded_answer(evidence, gene_name, question):
    """
    Deterministic evidence-based assistant.

    This is intentionally NOT an LLM.
    It answers only from retrieved V1 evidence.
    """

    if not evidence:
        return (
            f"I could not find sufficient evidence for {gene_name} "
            "in the available V1 datasets."
        )

    integrated = evidence.get("integrated_ranking", {})
    top15 = evidence.get("top15", {})
    roc = evidence.get("roc_validation", {})
    ml = evidence.get("machine_learning", {})
    stability = evidence.get("stability", {})
    de = evidence.get("differential_expression", {})
    validation = evidence.get("independent_validation", {})

    q = question.lower()

    # --------------------------------------------------------
    # WHY IS THIS A BIOMARKER?
    # --------------------------------------------------------

    if (
        "why" in q
        or "biomarker" in q
        or "strong" in q
        or "candidate" in q
    ):
        answer = f"""
### Evidence summary for {gene_name}

**{gene_name}** is supported by multiple independent evidence
components in the existing V1 pipeline.

- **Validation rank:** {top15.get("validation_rank", "N/A")}
- **Validation status:** {top15.get("validation_status", "N/A")}
- **ROC-AUC:** {_fmt(roc.get("AUC"))}
- **Sensitivity:** {_fmt(roc.get("sensitivity"))}
- **Specificity:** {_fmt(roc.get("specificity"))}
- **ML rank:** {ml.get("ML_rank", "N/A")}
- **Feature importance:** {_fmt(ml.get("importance"))}
- **Stability score:** {_fmt(stability.get("stability_score"))}
- **log₂ fold change:** {_fmt(de.get("log2FoldChange"))}
- **Adjusted p-value:** {_fmt(de.get("padj"), 6)}

The V1 pipeline therefore provides evidence from differential
expression, independent validation, ROC performance, machine
learning, and stability.

The official integrated ranking is:

**Integrated score:** {_fmt(integrated.get("integrated_score"))}

**Integrated rank:** {integrated.get("integrated_rank", "N/A")}

This summary describes the available computational evidence.
It does not establish clinical validity or replace experimental
validation.
"""

        return answer.strip()

    # --------------------------------------------------------
    # ROC QUESTION
    # --------------------------------------------------------

    if "auc" in q or "roc" in q or "sensitivity" in q or "specificity" in q:
        return f"""
### ROC / Validation evidence for {gene_name}

- **AUC:** {_fmt(roc.get("AUC"))}
- **Sensitivity:** {_fmt(roc.get("sensitivity"))}
- **Specificity:** {_fmt(roc.get("specificity"))}

These values come directly from the V1 ROC/validation output.

No new ROC calculation is performed by V2.
""".strip()

    # --------------------------------------------------------
    # MACHINE LEARNING QUESTION
    # --------------------------------------------------------

    if "machine learning" in q or "ml" in q or "importance" in q:
        return f"""
### Machine-learning evidence for {gene_name}

- **ML rank:** {ml.get("ML_rank", "N/A")}
- **Feature importance:** {_fmt(ml.get("importance"))}

These values come directly from the V1 machine-learning output.

V2 does not retrain the model or modify the ML ranking.
""".strip()

    # --------------------------------------------------------
    # STABILITY QUESTION
    # --------------------------------------------------------

    if "stability" in q or "stable" in q:
        return f"""

### Stability evidence for {gene_name}

The V1 biomarker stability analysis provides several measures of
how consistently this biomarker was selected across machine-learning
validation folds.

- **Stability score:** {_fmt(stability.get("stability_score"), 4)}
- **Stability rank:** {stability.get("stability_rank", "N/A")}
- **Top-10 stability:** {_fmt(stability.get("top10_stability"), 2)}
- **Top-20 stability:** {_fmt(stability.get("top20_stability"), 2)}
- **Mean Random-Forest importance:** {_fmt(stability.get("mean_rf_importance"), 4)}
- **SD Random-Forest importance:** {_fmt(stability.get("sd_rf_importance"), 4)}
- **Mean permutation importance:** {_fmt(stability.get("mean_permutation_importance"), 4)}
- **SD permutation importance:** {_fmt(stability.get("sd_permutation_importance"), 4)}
- **Normalized Random-Forest score:** {_fmt(stability.get("normalized_rf"), 4)}
- **Normalized permutation score:** {_fmt(stability.get("normalized_permutation"), 4)}

These values come directly from the V1 biomarker stability analysis.

V2 does not recalculate or modify the stability metrics.
""".strip()

    # --------------------------------------------------------
    # DIFFERENTIAL EXPRESSION QUESTION
    # --------------------------------------------------------

    if (
        "expression" in q
        or "fold change" in q
        or "log2" in q
        or "deg" in q
    ):
        return f"""
### Differential-expression evidence for {gene_name}

- **Base mean:** {_fmt(de.get("baseMean"))}
- **log₂ fold change:** {_fmt(de.get("log2FoldChange"))}
- **p-value:** {_fmt(de.get("pvalue"), 6)}
- **Adjusted p-value:** {_fmt(de.get("padj"), 6)}

These values come directly from the V1 differential-expression
results.
""".strip()

    # --------------------------------------------------------
    # DEFAULT RESPONSE
    # --------------------------------------------------------

    return f"""
### Evidence available for {gene_name}

I found evidence for this biomarker in the V1-derived datasets.

The available evidence includes:

- Integrated ranking
- Biomarker validation
- ROC/AUC
- Machine learning
- Stability
- Differential expression

Try asking a more specific question, such as:

**"Why is {gene_name} a strong biomarker candidate?"**

or:

**"What is the ROC-AUC for {gene_name}?"**

or:

**"What is the machine-learning evidence for {gene_name}?"**
""".strip()


def show_ai_assistant(data):

    st.title("🤖 AI Biomarker Assistant")

    st.markdown(
        """
        Ask questions about the computational evidence supporting
        individual LUAD biomarker candidates.

        **Important:** This assistant is grounded in the existing
        V1 pipeline outputs. It does not recalculate biological
        results or invent evidence.
        """
    )

    st.divider()

    top15 = data.get("top15")

    if top15 is None or top15.empty:
        st.error("Biomarker data are unavailable.")
        return

    genes = (
        top15["gene_name"]
        .dropna()
        .astype(str)
        .tolist()
    )

    gene = st.selectbox(
        "🧬 Select a biomarker",
        genes,
        key="ai_assistant_gene",
    )

    selected = top15[
        top15["gene_name"] == gene
    ].iloc[0]

    st.subheader(f"🔬 {gene}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Validation Rank",
            selected.get("validation_rank", "N/A"),
        )

    with col2:
        auc = selected.get("AUC")

        if auc is not None:
            st.metric(
                "ROC-AUC",
                f"{float(auc):.3f}",
            )
        else:
            st.metric("ROC-AUC", "N/A")

    with col3:
        st.metric(
            "ML Rank",
            selected.get("ML_rank", "N/A"),
        )

    with col4:
        stability = selected.get("stability_score")

        if stability is not None:
            st.metric(
                "Stability",
                f"{float(stability):.3f}",
            )
        else:
            st.metric("Stability", "N/A")

    st.divider()

    st.subheader("💬 Ask about this biomarker")

    question = st.text_input(
        "Ask a question",
        value=f"Why is {gene} a strong biomarker candidate?",
        key="ai_assistant_question",
    )

    st.caption(
        "Examples: ROC-AUC, machine-learning evidence, "
        "stability, differential expression, or overall evidence."
    )

    if st.button(
        "🔎 Analyze Evidence",
        type="primary",
        key="analyze_evidence_button",
    ):

        evidence = get_biomarker_evidence(
            data,
            gene,
        )

        grounded = build_grounded_context(
            evidence,
            gene,
        )

        answer = generate_grounded_answer(
            evidence,
            gene,
            question,
        )

        st.divider()

        st.subheader("🧠 Evidence-Grounded Answer")

        st.markdown(answer)

        st.divider()

        st.subheader("🔒 AI Grounding")

        st.success(
            "Answer generated only from the retrieved V1 biomarker evidence."
        )

        with st.expander("📚 Evidence sources used"):

            if grounded:
                st.markdown(grounded)

            else:
                st.info(
                    "No grounding context was available."
                )
