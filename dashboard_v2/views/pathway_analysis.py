import streamlit as st
import pandas as pd


def _show_pathway_table(df, title):
    if df is None or df.empty:
        st.info(f"No {title} pathway results are available.")
        return

    st.subheader(title)

    preferred = [
        "GOID",
        "TERM",
        "GeneRatio",
        "BgRatio",
        "FoldEnrichment",
        "pvalue",
        "padj",
        "contributing_genes",
        "ID",
        "Description",
        "p.adjust",
        "qvalue",
        "Count",
        "geneID",
    ]

    columns = [
        col for col in preferred
        if col in df.columns
    ]

    if not columns:
        columns = list(df.columns)

    st.dataframe(
        df[columns],
        use_container_width=True,
        hide_index=True,
    )


def _show_enrichment_plot(df, title):
    """Display a robust enrichment dot plot for pathway results."""
    if df is None or df.empty:
        return

    import numpy as np
    import plotly.express as px

    plot_df = df.copy()

    # Accept both the customer-engine column names and
    # common enrichment-tool column names.
    if "TERM" not in plot_df.columns:
        if "Description" in plot_df.columns:
            plot_df["TERM"] = plot_df["Description"]
        elif "term" in plot_df.columns:
            plot_df["TERM"] = plot_df["term"]

    if "Hits" not in plot_df.columns:
        if "Count" in plot_df.columns:
            plot_df["Hits"] = plot_df["Count"]

    if "padj" not in plot_df.columns:
        if "p.adjust" in plot_df.columns:
            plot_df["padj"] = plot_df["p.adjust"]
        elif "pvalue" in plot_df.columns:
            plot_df["padj"] = plot_df["pvalue"]

    if "FoldEnrichment" not in plot_df.columns:
        # Calculate fold enrichment when GeneRatio/BgRatio exist.
        if "GeneRatio" in plot_df.columns and "BgRatio" in plot_df.columns:
            gr = pd.to_numeric(
                plot_df["GeneRatio"],
                errors="coerce",
            )
            br = pd.to_numeric(
                plot_df["BgRatio"],
                errors="coerce",
            )
            plot_df["FoldEnrichment"] = gr / br

    required = {
        "TERM",
        "FoldEnrichment",
        "Hits",
        "padj",
    }

    if not required.issubset(plot_df.columns):
        st.warning(
            f"{title} results are available, but the chart cannot "
            f"be rendered because required plotting columns are missing."
        )
        return

    plot_df["TERM"] = (
        plot_df["TERM"]
        .astype(str)
        .str.strip()
    )

    plot_df["FoldEnrichment"] = pd.to_numeric(
        plot_df["FoldEnrichment"],
        errors="coerce",
    )

    plot_df["Hits"] = pd.to_numeric(
        plot_df["Hits"],
        errors="coerce",
    )

    plot_df["padj"] = pd.to_numeric(
        plot_df["padj"],
        errors="coerce",
    )

    plot_df = plot_df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    plot_df = plot_df.dropna(
        subset=[
            "TERM",
            "FoldEnrichment",
            "Hits",
            "padj",
        ]
    )

    plot_df = plot_df[
        (plot_df["TERM"] != "") &
        (plot_df["FoldEnrichment"] >= 0) &
        (plot_df["Hits"] > 0) &
        (plot_df["padj"] >= 0)
    ]

    if plot_df.empty:
        st.warning(
            f"{title} pathway results are available, but there "
            f"are no valid numeric values available for plotting."
        )
        return

    # Prevent extremely small/zero adjusted p-values from
    # producing infinite -log10 values.
    plot_df["FDR_display"] = plot_df["padj"].clip(
        lower=1e-300
    )

    plot_df["-log10(FDR)"] = (
        -np.log10(plot_df["FDR_display"])
    )

    # Keep the strongest pathways.
    plot_df = plot_df.sort_values(
        ["padj", "FoldEnrichment"],
        ascending=[True, False],
    ).head(10)

    # Horizontal ordering: strongest enrichment at the top.
    plot_df = plot_df.sort_values(
        "FoldEnrichment",
        ascending=True,
    )

    hover_data = {
        "FoldEnrichment": ":.2f",
        "Hits": True,
        "padj": ":.3g",
    }

    if "contributing_genes" in plot_df.columns:
        hover_data["contributing_genes"] = True

    fig = px.scatter(
        plot_df,
        x="FoldEnrichment",
        y="TERM",
        size="Hits",
        color="-log10(FDR)",
        hover_data=hover_data,
        title=f"Top Enriched {title}",
        labels={
            "FoldEnrichment": "Fold enrichment",
            "TERM": "GO term",
            "-log10(FDR)": "−log10(FDR)",
            "Hits": "Genes",
        },
        height=max(
            420,
            55 * len(plot_df) + 160,
        ),
    )

    fig.update_traces(
        marker=dict(
            sizemin=8,
            line=dict(width=0.5),
        )
    )

    fig.update_layout(
        margin=dict(
            l=20,
            r=30,
            t=80,
            b=30,
        ),
        yaxis=dict(
            title="",
            automargin=True,
            type="category",
        ),
        xaxis=dict(
            title="Fold enrichment",
            rangemode="tozero",
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "responsive": True,
        },
    )


def _show_customer_pathway_analysis(customer_context):
    from core.customer_pathway import (
        CustomerPathwayError,
        run_customer_go_enrichment,
    )

    st.title("🧪 Pathway Analysis")

    st.markdown(
        f"""
        Explore biological pathway enrichment associated with
        biomarker candidates identified from the uploaded
        **{customer_context.cancer_type}** dataset.

        **Comparison:** {customer_context.comparison}

        Enrichment is calculated using the uploaded expression
        genes as the background universe and the differential-
        expression candidates as the enrichment set.
        """
    )

    st.info(
        "These pathway results are exploratory biological evidence "
        "from the uploaded dataset. They are not independent "
        "clinical validation."
    )

    st.divider()

    try:
        cache_key = "onconexa_customer_pathway_cache"
        cached = st.session_state.get(cache_key)

        if (
            cached is None
            or cached.get("analysis_id") != customer_context.analysis_id
        ):
            result = run_customer_go_enrichment(
                expression_data=customer_context.expression_data,
                differential_expression=(
                    customer_context.differential_expression
                ),
                gene_column=customer_context.gene_column,
            )

            st.session_state[cache_key] = {
                "analysis_id": customer_context.analysis_id,
                "result": result,
            }
        else:
            result = cached["result"]

    except CustomerPathwayError as exc:
        st.error(str(exc))
        return

    except Exception as exc:
        st.error(
            f"Pathway analysis could not be completed: {exc}"
        )
        return

    go_bp = result.get("BP", pd.DataFrame())
    go_cc = result.get("CC", pd.DataFrame())
    go_mf = result.get("MF", pd.DataFrame())

    st.subheader("📊 Enrichment Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "GO Biological Process",
            len(go_bp),
        )

    with col2:
        st.metric(
            "GO Cellular Component",
            len(go_cc),
        )

    with col3:
        st.metric(
            "GO Molecular Function",
            len(go_mf),
        )

    with col4:
        st.metric(
            "Mapped Candidates",
            result.get("candidate_size", 0),
        )

    st.caption(
        f"Background genes mapped: "
        f"{result.get('background_size', 0)}"
    )

    st.divider()

    tab1, tab2, tab3 = st.tabs(
        [
            "🧬 GO Biological Process",
            "🧫 GO Cellular Component",
            "⚙️ GO Molecular Function",
        ]
    )

    with tab1:
        _show_enrichment_plot(
            go_bp,
            "GO Biological Process",
        )
        _show_pathway_table(
            go_bp,
            "GO Biological Process",
        )

    with tab2:
        _show_enrichment_plot(
            go_cc,
            "GO Cellular Component",
        )
        _show_pathway_table(
            go_cc,
            "GO Cellular Component",
        )

    with tab3:
        _show_enrichment_plot(
            go_mf,
            "GO Molecular Function",
        )
        _show_pathway_table(
            go_mf,
            "GO Molecular Function",
        )

    st.divider()

    st.caption(
        "Data provenance: uploaded expression data + "
        "differential-expression candidates + local "
        "org.Hs.eg.db / GO.db annotation."
    )


def show_pathway_analysis(data):

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    if (
        customer_context is not None
        and customer_context.has_differential_expression()
    ):
        _show_customer_pathway_analysis(customer_context)
        return

    st.title("🧪 Pathway Analysis")

    st.markdown(
        """
        Explore biological pathways associated with the LUAD
        biomarker candidates.

        Results are derived from the existing V1 pathway-enrichment
        analysis and are presented without recalculating enrichment.
        """
    )

    st.divider()

    go_bp = data.get("go_bp")
    go_cc = data.get("go_cc")
    go_mf = data.get("go_mf")
    kegg = data.get("kegg")

    st.subheader("📊 Enrichment Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "GO Biological Process",
            len(go_bp) if go_bp is not None else 0,
        )

    with col2:
        st.metric(
            "GO Cellular Component",
            len(go_cc) if go_cc is not None else 0,
        )

    with col3:
        st.metric(
            "GO Molecular Function",
            len(go_mf) if go_mf is not None else 0,
        )

    with col4:
        st.metric(
            "KEGG Pathways",
            len(kegg) if kegg is not None else 0,
        )

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🧬 GO Biological Process",
            "🧫 GO Cellular Component",
            "⚙️ GO Molecular Function",
            "🛤️ KEGG",
        ]
    )

    with tab1:
        _show_pathway_table(
            go_bp,
            "GO Biological Process",
        )

    with tab2:
        _show_pathway_table(
            go_cc,
            "GO Cellular Component",
        )

    with tab3:
        _show_pathway_table(
            go_mf,
            "GO Molecular Function",
        )

    with tab4:
        _show_pathway_table(
            kegg,
            "KEGG Pathways",
        )

    st.divider()

    st.caption(
        "Data provenance: canonical V1 pathway-enrichment outputs • "
        "V2 presentation layer"
    )
