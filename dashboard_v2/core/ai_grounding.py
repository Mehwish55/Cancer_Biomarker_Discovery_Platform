import json


# ============================================================
# AI GROUNDING LAYER
# ============================================================

def _format_value(value):
    """Convert values into safe, readable text."""

    if value is None:
        return "N/A"

    try:
        if isinstance(value, float):
            return f"{value:.6f}"
    except (TypeError, ValueError):
        pass

    return str(value)


def build_grounded_context(evidence, gene_name):
    """
    Build a structured evidence context for a future AI assistant.

    IMPORTANT:
    This function does not generate biological claims.
    It only packages evidence retrieved from the V1-derived
    evidence engine.
    """

    if not evidence:
        return {
            "gene": gene_name,
            "evidence_available": False,
            "context": "",
            "sources": [],
        }

    sections = []
    sources = []

    # --------------------------------------------------------
    # Integrated Ranking
    # --------------------------------------------------------

    integrated = evidence.get(
        "integrated_ranking",
        {},
    )

    if integrated:
        sections.append(
            "INTEGRATED RANKING:\n"
            f"Integrated score: "
            f"{_format_value(integrated.get('integrated_score'))}\n"
            f"Integrated rank: "
            f"{_format_value(integrated.get('integrated_rank'))}\n"
            f"AUC score component: "
            f"{_format_value(integrated.get('score_AUC'))}\n"
            f"Sensitivity score component: "
            f"{_format_value(integrated.get('score_sensitivity'))}\n"
            f"Specificity score component: "
            f"{_format_value(integrated.get('score_specificity'))}\n"
            f"Stability score component: "
            f"{_format_value(integrated.get('score_stability'))}\n"
            f"ML score component: "
            f"{_format_value(integrated.get('score_ML'))}\n"
            f"DE score component: "
            f"{_format_value(integrated.get('score_DE'))}"
        )

        sources.append("integrated_ranking")

    # --------------------------------------------------------
    # Top 15
    # --------------------------------------------------------

    top15 = evidence.get(
        "top15",
        {},
    )

    if top15:
        sections.append(
            "TOP BIOMARKER EVIDENCE:\n"
            f"Validation rank: "
            f"{_format_value(top15.get('validation_rank'))}\n"
            f"Validation status: "
            f"{_format_value(top15.get('validation_status'))}\n"
            f"AUC: "
            f"{_format_value(top15.get('AUC'))}\n"
            f"Stability score: "
            f"{_format_value(top15.get('stability_score'))}\n"
            f"ML rank: "
            f"{_format_value(top15.get('ML_rank'))}\n"
            f"log2FoldChange: "
            f"{_format_value(top15.get('log2FoldChange'))}\n"
            f"Adjusted p-value: "
            f"{_format_value(top15.get('padj'))}"
        )

        sources.append("top15")

    # --------------------------------------------------------
    # ROC / Validation
    # --------------------------------------------------------

    roc = evidence.get(
        "roc_validation",
        {},
    )

    if roc:
        sections.append(
            "ROC / VALIDATION:\n"
            f"AUC: "
            f"{_format_value(roc.get('AUC'))}\n"
            f"Sensitivity: "
            f"{_format_value(roc.get('sensitivity'))}\n"
            f"Specificity: "
            f"{_format_value(roc.get('specificity'))}"
        )

        sources.append("roc_validation")

    # --------------------------------------------------------
    # Independent Validation
    # --------------------------------------------------------

    validation = evidence.get(
        "independent_validation",
        {},
    )

    if validation:
        sections.append(
            "INDEPENDENT VALIDATION:\n"
            f"Direction: "
            f"{_format_value(validation.get('direction'))}\n"
            f"Validation status: "
            f"{_format_value(validation.get('validation_status'))}"
        )

        sources.append("independent_validation")

    # --------------------------------------------------------
    # Machine Learning
    # --------------------------------------------------------

    ml = evidence.get(
        "machine_learning",
        {},
    )

    if ml:
        sections.append(
            "MACHINE LEARNING:\n"
            f"Feature importance: "
            f"{_format_value(ml.get('importance'))}\n"
            f"ML rank: "
            f"{_format_value(ml.get('ML_rank'))}"
        )

        sources.append("machine_learning")

    # --------------------------------------------------------
    # Stability
    # --------------------------------------------------------

    stability = evidence.get(
        "stability",
        {},
    )

    if stability:
        sections.append(
            "STABILITY:\n"
            f"Stability score: "
            f"{_format_value(stability.get('stability_score'))}"
        )

        sources.append("stability")

    # --------------------------------------------------------
    # Differential Expression
    # --------------------------------------------------------

    de = evidence.get(
        "differential_expression",
        {},
    )

    if de:
        sections.append(
            "DIFFERENTIAL EXPRESSION:\n"
            f"Base mean: "
            f"{_format_value(de.get('baseMean'))}\n"
            f"log2FoldChange: "
            f"{_format_value(de.get('log2FoldChange'))}\n"
            f"p-value: "
            f"{_format_value(de.get('pvalue'))}\n"
            f"Adjusted p-value: "
            f"{_format_value(de.get('padj'))}"
        )

        sources.append("differential_expression")

    # --------------------------------------------------------
    # Safety instructions for future AI
    # --------------------------------------------------------

    system_instructions = """
GROUNDING RULES:

1. Use only evidence contained in this context.
2. Do not invent numerical values.
3. Do not invent experimental results.
4. Do not claim evidence exists when it is absent.
5. Clearly distinguish pipeline-derived results from interpretation.
6. Do not recalculate or modify the official integrated ranking.
7. If the available evidence is insufficient to answer a question,
   explicitly say that the available data are insufficient.
8. Do not present biological interpretation as experimentally proven.
9. When discussing a numerical result, use the value provided here.
10. This context is evidence retrieval, not a substitute for
    experimental validation.
"""

    context = (
        f"BIOMARKER: {gene_name}\n\n"
        + "\n\n".join(sections)
        + "\n\n"
        + system_instructions.strip()
    )

    return {
        "gene": gene_name,
        "evidence_available": True,
        "sources": sources,
        "context": context,
    }


def context_as_json(grounded_context):
    """
    Convert grounded context to JSON.

    Useful later when connecting an LLM API.
    """

    return json.dumps(
        grounded_context,
        indent=2,
        default=str,
    )
