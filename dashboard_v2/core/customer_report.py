from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


def _clean(value: Any, default: str = "—") -> str:
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    text = str(value).strip()
    return text if text else default


def _format_number(value: Any, digits: int = 3) -> str:
    try:
        number = float(value)
        if pd.isna(number):
            return "—"
        return f"{number:,.{digits}f}"
    except Exception:
        return _clean(value)


def _format_scientific(value: Any) -> str:
    try:
        number = float(value)
        if pd.isna(number):
            return "—"
        return f"{number:.3e}"
    except Exception:
        return _clean(value)


def _df_from(value: Any) -> pd.DataFrame | None:
    if isinstance(value, pd.DataFrame) and not value.empty:
        return value.copy()

    if isinstance(value, list) and value:
        try:
            frame = pd.DataFrame(value)
            return frame if not frame.empty else None
        except Exception:
            return None

    if isinstance(value, dict) and value:
        try:
            frame = pd.DataFrame(value)
            return frame if not frame.empty else None
        except Exception:
            return None

    return None


def _table(
    dataframe: pd.DataFrame,
    columns: list[str],
    max_rows: int = 12,
) -> Table | None:
    available = [c for c in columns if c in dataframe.columns]

    if not available:
        return None

    frame = dataframe[available].head(max_rows).copy()

    display_rows = []

    for _, row in frame.iterrows():
        values = []

        for column in available:
            value = row[column]

            if column.lower() in {"padj", "pvalue", "p_value", "p-value"}:
                values.append(_format_scientific(value))
            elif isinstance(value, (int, float)):
                values.append(_format_number(value))
            else:
                values.append(_clean(value))

        display_rows.append(values)

    headers = [
        Paragraph(
            str(column).replace("_", " ").title(),
            _styles()["table_header"],
        )
        for column in available
    ]

    body = [headers]

    for row in display_rows:
        body.append(
            [
                Paragraph(str(value), _styles()["table_cell"])
                for value in row
            ]
        )

    widths = [180 * mm / len(available)] * len(available)

    table = Table(
        body,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E1EA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F5F8FB"),
                ]),
            ]
        )
    )

    return table


def _styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "OncoTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "OncoSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#5B6573"),
            spaceAfter=18,
        ),
        "section": ParagraphStyle(
            "OncoSection",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=8,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "OncoH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#17365D"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "OncoH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#24527A"),
            spaceBefore=7,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "OncoBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#28323C"),
            spaceAfter=6,
        ),
        "metric": ParagraphStyle(
            "OncoMetric",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#17365D"),
        ),
        "table_header": ParagraphStyle(
            "OncoTableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "OncoTableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor("#28323C"),
        ),
        "small": ParagraphStyle(
            "OncoSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#5B6573"),
        ),
    }


def _footer(canvas, doc):
    canvas.saveState()

    width, height = A4

    # ============================================================
    # FOOTER
    # ============================================================

    canvas.setStrokeColor(colors.HexColor("#D9E1EA"))
    canvas.setLineWidth(0.5)
    canvas.line(
        18 * mm,
        13 * mm,
        width - 18 * mm,
        13 * mm,
    )

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#6B7280"))

    canvas.drawString(
        18 * mm,
        8 * mm,
        "OncoNexa — AI-Powered Pan-Cancer Biomarker Discovery Platform",
    )

    canvas.drawRightString(
        width - 18 * mm,
        8 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()

def build_customer_report(
    customer_context,
    roc_results=None,
    ml_results=None,
    stability_results=None,
    pathway_cache=None,
) -> bytes:
    """
    Generate a professional customer-specific OncoNexa PDF report.

    The function is deliberately tolerant of missing downstream analyses.
    Existing analysis engines are not modified.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="OncoNexa Customer Biomarker Analysis Report",
        author="OncoNexa",
    )

    styles = _styles()
    story = []

    cancer_type = _clean(
        getattr(customer_context, "cancer_type", None),
        "Customer Cancer Dataset",
    )

    comparison = _clean(
        getattr(customer_context, "comparison", None),
        "Group comparison",
    )

    analysis_type = _clean(
        getattr(customer_context, "analysis_type", None),
        "RNA-seq analysis",
    )

    analysis_id = _clean(
        getattr(customer_context, "analysis_id", None),
        "Not available",
    )

    expression = getattr(customer_context, "expression_data", None)
    metadata = getattr(customer_context, "metadata", None)
    deg = getattr(customer_context, "differential_expression", None)

    n_samples = (
        len(getattr(customer_context, "sample_columns", []) or [])
    )

    if n_samples == 0 and isinstance(expression, pd.DataFrame):
        n_samples = max(len(expression.columns) - 1, 0)

    n_degs = (
        len(deg)
        if isinstance(deg, pd.DataFrame)
        else 0
    )

    # ============================================================
    # COVER
    # ============================================================

    # Professional cover-page border.
    # This is applied only to the first page through the canvas callback.
    story.append(Spacer(1, 8 * mm))

    story.append(
        Paragraph(
            "OncoNexa",
            styles["title"],
        )
    )

    story.append(
        Spacer(1, 2 * mm)
    )

    story.append(
        Paragraph(
            "AI-Powered Pan-Cancer Biomarker Discovery Platform",
            styles["subtitle"],
        )
    )

    story.append(
        Spacer(1, 9 * mm)
    )

    customer_box = Table(
        [
            [
                Paragraph(
                    "<b>CUSTOMER DATASET</b>",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Cancer / Dataset:</b> {_clean(cancer_type)}",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Comparison:</b> {_clean(comparison)}",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Analysis:</b> {_clean(analysis_type)}",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Samples Analyzed:</b> {n_samples}",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Significant DE Results:</b> {n_degs}",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Analysis ID:</b> {analysis_id}",
                    styles["body"],
                )
            ],
            [
                Paragraph(
                    f"<b>Report Generated:</b> "
                    f"{datetime.now().strftime('%d %B %Y')}",
                    styles["body"],
                )
            ],
        ],
        colWidths=[174 * mm],
        hAlign="CENTER",
    )

    customer_box.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF2F8"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1.0,
                    colors.HexColor("#7F9DB9"),
                ),
                (
                    "INNERGRID",
                    (0, 1),
                    (-1, -1),
                    0.3,
                    colors.HexColor("#D9E1EA"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(customer_box)

    story.append(
        Spacer(1, 15 * mm)
    )

    story.append(
        Paragraph(
            "<b>CONFIDENTIAL CUSTOMER ANALYSIS</b>",
            styles["small"],
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            "Prepared by OncoNexa",
            styles["small"],
        )
    )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Analysis Summary",
            styles["section"],
        )
    )

    # ============================================================
    # ANALYSIS SUMMARY
    # ============================================================

    story.append(
        Paragraph("1. Analysis Summary", styles["h1"])
    )

    summary_rows = [
        ["Metric", "Value"],
        ["Cancer / dataset", cancer_type],
        ["Comparison", comparison],
        ["Analysis type", analysis_type],
        ["Samples", str(n_samples)],
        ["Differential-expression results", str(n_degs)],
        ["Analysis ID", analysis_id],
    ]

    summary_table = Table(
        summary_rows,
        colWidths=[85 * mm, 89 * mm],
        repeatRows=1,
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D9E1EA")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F5F8FB"),
                ]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(summary_table)

    # ============================================================
    # DIFFERENTIAL EXPRESSION
    # ============================================================

    if isinstance(deg, pd.DataFrame) and not deg.empty:

        story.append(
            Paragraph(
                "2. Differential Expression",
                styles["h1"],
            )
        )

        significant = deg.copy()

        if "padj" in significant.columns:
            significant["padj"] = pd.to_numeric(
                significant["padj"],
                errors="coerce",
            )
            significant = significant[
                significant["padj"].notna()
                & (significant["padj"] < 0.05)
            ]

        up = 0
        down = 0

        if "direction" in significant.columns:
            direction = significant["direction"].astype(str).str.lower()
            up = int(direction.str.contains("up").sum())
            down = int(direction.str.contains("down").sum())

        metric_table = Table(
            [
                [
                    Paragraph("Significant DEGs", styles["metric"]),
                    Paragraph("Upregulated", styles["metric"]),
                    Paragraph("Downregulated", styles["metric"]),
                ],
                [
                    str(len(significant)),
                    str(up),
                    str(down),
                ],
            ],
            colWidths=[58 * mm, 58 * mm, 58 * mm],
        )

        metric_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2F8")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#B8C7D9")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E1EA")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )

        story.append(metric_table)
        story.append(Spacer(1, 5 * mm))

        de_columns = [
            column
            for column in [
                "gene",
                "log2FoldChange",
                "pvalue",
                "padj",
                "direction",
            ]
            if column in significant.columns
        ]

        de_table = _table(
            significant,
            de_columns,
            max_rows=15,
        )

        if de_table:
            story.append(
                Paragraph(
                    "Top Differentially Expressed Genes",
                    styles["h2"],
                )
            )
            story.append(de_table)

    # ============================================================
    # ROC
    # ============================================================

    roc = _df_from(roc_results)

    if roc is not None:

        story.append(
            Paragraph(
                "3. Biomarker Discrimination",
                styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "ROC/AUC results are calculated within the uploaded "
                "customer dataset and should not be interpreted as "
                "independent-cohort validation.",
                styles["body"],
            )
        )

        roc_columns = [
            column
            for column in [
                "ROC_rank",
                "gene_name",
                "AUC",
                "CI_lower",
                "CI_upper",
                "pvalue",
                "sensitivity",
                "specificity",
                "direction",
            ]
            if column in roc.columns
        ]

        roc_table = _table(
            roc,
            roc_columns,
            max_rows=15,
        )

        if roc_table:
            story.append(roc_table)

    # ============================================================
    # ML
    # ============================================================

    ml = _df_from(ml_results)

    if ml is not None:

        story.append(
            Paragraph(
                "4. Machine Learning Results",
                styles["h1"],
            )
        )

        ml_table = _table(
            ml,
            list(ml.columns[:8]),
            max_rows=15,
        )

        if ml_table:
            story.append(ml_table)

    # ============================================================
    # STABILITY
    # ============================================================

    stability = _df_from(stability_results)

    if stability is not None:

        story.append(
            Paragraph(
                "5. Biomarker Stability",
                styles["h1"],
            )
        )

        story.append(
            Paragraph(
                "Stability results summarize the consistency of candidate "
                "biomarkers under repeated resampling or the corresponding "
                "OncoNexa stability workflow.",
                styles["body"],
            )
        )

        stability_table = _table(
            stability,
            list(stability.columns[:8]),
            max_rows=15,
        )

        if stability_table:
            story.append(stability_table)

    # ============================================================
    # PATHWAY
    # ============================================================

    pathway = _df_from(pathway_cache)

    if pathway is not None:

        story.append(
            Paragraph(
                "6. Functional Biology",
                styles["h1"],
            )
        )

        pathway_table = _table(
            pathway,
            list(pathway.columns[:8]),
            max_rows=15,
        )

        if pathway_table:
            story.append(pathway_table)

    # ============================================================
    # FINAL NOTES
    # ============================================================

    story.append(
        Paragraph(
            "7. Interpretation & Next Steps",
            styles["h1"],
        )
    )

    story.append(
        Paragraph(
            "Candidate biomarkers should be prioritized using the "
            "combined evidence available in the OncoNexa workflow, "
            "including differential expression, discrimination, machine "
            "learning, stability and functional biology where available.",
            styles["body"],
        )
    )

    story.append(
        Paragraph(
            "This report is an analytical research output and does not "
            "constitute a clinical diagnosis, treatment recommendation, "
            "or regulatory validation.",
            styles["small"],
        )
    )

    document.build(
        story,
        onFirstPage=_footer,
        onLaterPages=_footer,
    )

    return buffer.getvalue()
