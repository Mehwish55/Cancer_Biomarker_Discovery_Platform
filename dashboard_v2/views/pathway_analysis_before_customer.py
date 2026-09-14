import streamlit as st
import pandas as pd


def _show_pathway_table(df, title):
    if df is None or df.empty:
        st.info(f"No {title} pathway results are available.")
        return

    st.subheader(title)

    # Prefer the most informative columns when available
    preferred = [
        "ID",
        "Description",
        "GeneRatio",
        "BgRatio",
        "pvalue",
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


def show_pathway_analysis(data):

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

    # --------------------------------------------------
    # Overview
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Tabs
    # --------------------------------------------------

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
