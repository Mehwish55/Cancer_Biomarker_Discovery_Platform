import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


def show_differential_expression(deg):

    # ==================================================
    # CUSTOMER CONTEXT
    # ==================================================

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    if (
        customer_context is not None
        and customer_context.has_differential_expression()
    ):
        deg = customer_context.differential_expression

        raw_cancer_type = customer_context.cancer_type
        analysis_label = (
            str(raw_cancer_type).strip()
            if raw_cancer_type is not None
            and str(raw_cancer_type).strip()
            else "Uploaded Dataset"
        )

        raw_comparison = customer_context.comparison
        comparison_label = (
            str(raw_comparison).strip()
            if raw_comparison is not None
            and str(raw_comparison).strip()
            else "Group comparison"
        )

        is_customer_analysis = True
    else:
        analysis_label = "LUAD"
        comparison_label = "Tumor vs Normal"
        is_customer_analysis = False

    st.title("📊 Differential Expression Analysis")

    if is_customer_analysis:
        st.markdown(
            f"""
            Explore differential expression results for
            **{analysis_label}**.

            **Comparison:** {comparison_label}

            This analysis uses your uploaded dataset and the
            OncoNexa differential expression pipeline.
            """
        )
    else:
        st.markdown(
            """
            Explore the differential expression results from the LUAD
            tumor-versus-normal RNA-seq analysis.

            This page displays the **V1 pipeline results directly** and does
            not recalculate differential expression.
            """
        )

    if deg is None or deg.empty:
        st.error(
            "Differential expression data could not be loaded."
        )
        return

    # ==================================================
    # DATA PREPARATION
    # ==================================================

    df = deg.copy()

    # Customer DE output normally uses "gene".
    # Normalize locally for visualization only.
    if (
        "gene_name" not in df.columns
        and "gene" in df.columns
    ):
        df = df.rename(
            columns={"gene": "gene_name"}
        )

    # Numeric columns
    for column in [
        "log2FoldChange",
        "pvalue",
        "padj",
        "baseMean",
    ]:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # ==================================================
    # SIGNIFICANCE / DIRECTION
    # ==================================================

    if "padj" in df.columns:
        significant_mask = (
            df["padj"].notna()
            & (df["padj"] < 0.05)
        )
    else:
        significant_mask = pd.Series(
            True,
            index=df.index
        )

    if "log2FoldChange" in df.columns:
        upregulated = int(
            (
                significant_mask
                & (df["log2FoldChange"] > 0)
            ).sum()
        )

        downregulated = int(
            (
                significant_mask
                & (df["log2FoldChange"] < 0)
            ).sum()
        )
    else:
        upregulated = 0
        downregulated = 0

    significant = int(
        significant_mask.sum()
    )

    total_genes = len(df)

    # ==================================================
    # SUMMARY
    # ==================================================

    st.subheader("📈 Differential Expression Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Significant DEGs",
            f"{significant:,}"
        )

    with col2:
        st.metric(
            "Upregulated",
            f"{upregulated:,}"
        )

    with col3:
        st.metric(
            "Downregulated",
            f"{downregulated:,}"
        )

    with col4:
        st.metric(
            "Genes analyzed",
            f"{total_genes:,}"
        )

    st.divider()

    # ==================================================
    # FILTERS
    # ==================================================

    st.subheader("🔎 Explore Genes")

    col1, col2 = st.columns(2)

    with col1:
        search_gene = st.text_input(
            "Search gene",
            placeholder="e.g. EGFR, TP53, KRAS"
        )

    with col2:

        direction_options = ["All"]

        if "direction" in df.columns:
            direction_options += sorted(
                df["direction"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

        direction = st.selectbox(
            "Expression direction",
            direction_options
        )

    filtered = df.copy()

    # Gene search
    if search_gene.strip():

        if "gene_name" in filtered.columns:
            filtered = filtered[
                filtered["gene_name"]
                .astype(str)
                .str.contains(
                    search_gene.strip(),
                    case=False,
                    na=False
                )
            ]

    # Direction filter
    if (
        direction != "All"
        and "direction" in filtered.columns
    ):
        filtered = filtered[
            filtered["direction"].astype(str) == direction
        ]

    st.write(
        f"Showing **{len(filtered):,}** genes"
    )

    # ==================================================
    # VOLCANO PLOT
    # ==================================================

    if (
        "log2FoldChange" in df.columns
        and "padj" in df.columns
    ):

        plot_df = df.copy()

        plot_df["padj_plot"] = plot_df["padj"].clip(
            lower=1e-300
        )

        plot_df["-log10(FDR)"] = -np.log10(
            plot_df["padj_plot"]
        )

        plot_df["Expression"] = "Not significant"

        plot_df.loc[
            significant_mask
            & (plot_df["log2FoldChange"] > 0),
            "Expression"
        ] = "Upregulated"

        plot_df.loc[
            significant_mask
            & (plot_df["log2FoldChange"] < 0),
            "Expression"
        ] = "Downregulated"

        st.subheader("🌋 Differential Expression Landscape")

        fig = px.scatter(
            plot_df,
            x="log2FoldChange",
            y="-log10(FDR)",
            color="Expression",
            hover_data=[
                c
                for c in [
                    "gene_name",
                    "log2FoldChange",
                    "padj",
                    "pvalue",
                    "baseMean",
                ]
                if c in plot_df.columns
            ],
            title=(
                f"{analysis_label} Differential Expression"
            ),
        )

        fig.add_vline(
            x=1,
            line_dash="dash",
            opacity=0.5
        )

        fig.add_vline(
            x=-1,
            line_dash="dash",
            opacity=0.5
        )

        fig.add_hline(
            y=-np.log10(0.05),
            line_dash="dash",
            opacity=0.5
        )

        fig.update_layout(
            height=600,
            xaxis_title="log2 Fold Change",
            yaxis_title="-log10 Adjusted P-value",
            legend_title="Expression"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # ==================================================
    # MA PLOT
    # ==================================================

    ma_df = None
    ma_x_column = None
    ma_hover_columns = []

    # Preferred route: use baseMean when supplied by the DE engine.
    if (
        "baseMean" in df.columns
        and "log2FoldChange" in df.columns
    ):

        ma_df = df[
            [
                "baseMean",
                "log2FoldChange"
            ]
        ].copy()

        ma_df = ma_df[
            ma_df["baseMean"].notna()
            & ma_df["log2FoldChange"].notna()
            & (ma_df["baseMean"] > 0)
        ]

        ma_df["mean_expression"] = ma_df["baseMean"]
        ma_x_column = "mean_expression"
        ma_hover_columns = ["baseMean", "log2FoldChange"]

    # Customer fallback: calculate mean expression directly
    # from the uploaded expression matrix.
    elif (
        is_customer_analysis
        and "log2FoldChange" in df.columns
        and customer_context.expression_data is not None
        and not customer_context.expression_data.empty
    ):

        expression_df = customer_context.expression_data.copy()

        gene_column = (
            customer_context.gene_column
            if customer_context.gene_column
            in expression_df.columns
            else None
        )

        if gene_column is None:
            for candidate in [
                "gene",
                "gene_id",
                "gene_name",
                "symbol",
                "geneid"
            ]:
                if candidate in expression_df.columns:
                    gene_column = candidate
                    break

        if gene_column is not None:

            expression_df[gene_column] = (
                expression_df[gene_column]
                .astype(str)
            )

            numeric_expression = (
                expression_df
                .drop(columns=[gene_column])
                .apply(
                    pd.to_numeric,
                    errors="coerce"
                )
            )

            numeric_expression = (
                numeric_expression
                .select_dtypes(include=np.number)
            )

            if not numeric_expression.empty:

                mean_expression = (
                    numeric_expression
                    .mean(axis=1)
                    .rename("mean_expression")
                )

                expression_means = pd.DataFrame({
                    "gene_name": expression_df[
                        gene_column
                    ].astype(str),
                    "mean_expression": mean_expression
                })

                ma_df = df[
                    [
                        "gene_name",
                        "log2FoldChange"
                    ]
                ].copy()

                ma_df["gene_name"] = (
                    ma_df["gene_name"].astype(str)
                )

                ma_df = ma_df.merge(
                    expression_means,
                    on="gene_name",
                    how="inner"
                )

                ma_df = ma_df[
                    ma_df["mean_expression"].notna()
                    & ma_df["log2FoldChange"].notna()
                    & (ma_df["mean_expression"] > 0)
                ]

                ma_x_column = "mean_expression"
                ma_hover_columns = [
                    "mean_expression",
                    "log2FoldChange"
                ]

    if (
        ma_df is not None
        and not ma_df.empty
        and ma_x_column is not None
    ):

        ma_df["log10_mean_expression"] = np.log10(
            ma_df[ma_x_column]
        )

        st.subheader("📉 MA Plot")

        ma_fig = px.scatter(
            ma_df,
            x="log10_mean_expression",
            y="log2FoldChange",
            title=f"{analysis_label} MA Plot",
            opacity=0.65,
            hover_data=ma_hover_columns
        )

        ma_fig.add_hline(
            y=0,
            line_dash="dash",
            opacity=0.5
        )

        ma_fig.update_layout(
            height=550,
            xaxis_title="log10 Mean Expression",
            yaxis_title="log2 Fold Change"
        )

        st.plotly_chart(
            ma_fig,
            use_container_width=True
        )

    # ==================================================
    # TOP-GENE HEATMAP
    # ==================================================

    if is_customer_analysis:

        expression_df = customer_context.expression_data

        if (
            expression_df is not None
            and not expression_df.empty
            and "gene_name" in df.columns
        ):

            expression = expression_df.copy()

            gene_column = (
                customer_context.gene_column
                if customer_context.gene_column
                in expression.columns
                else None
            )

            if gene_column is None:

                for candidate in [
                    "gene",
                    "gene_id",
                    "gene_name",
                    "symbol",
                    "geneid"
                ]:
                    if candidate in expression.columns:
                        gene_column = candidate
                        break

            if gene_column is not None:

                expression[gene_column] = (
                    expression[gene_column]
                    .astype(str)
                )

                expression = expression.set_index(
                    gene_column
                )

                # Match DE genes to expression genes
                top_genes = (
                    df[
                        df["gene_name"].astype(str).isin(
                            expression.index.astype(str)
                        )
                    ]
                    .sort_values(
                        "padj",
                        ascending=True
                    )
                    .head(20)["gene_name"]
                    .astype(str)
                    .tolist()
                )

                if top_genes:

                    heatmap_data = expression.loc[
                        expression.index.astype(str).isin(
                            top_genes
                        )
                    ].copy()

                    # Keep only numeric sample columns
                    numeric_columns = (
                        heatmap_data
                        .select_dtypes(
                            include=np.number
                        )
                        .columns
                    )

                    heatmap_data = heatmap_data[
                        numeric_columns
                    ]

                    if (
                        not heatmap_data.empty
                        and heatmap_data.shape[1] > 1
                    ):

                        heatmap_data = heatmap_data.loc[
                            top_genes
                        ]

                        # Z-score each gene for visualization
                        heatmap_values = (
                            heatmap_data
                            .apply(
                                lambda row: (
                                    row - row.mean()
                                ) / (
                                    row.std()
                                    if row.std() != 0
                                    else 1
                                ),
                                axis=1
                            )
                        )

                        st.subheader(
                            "🔥 Top Biomarker Expression Heatmap"
                        )

                        heatmap_fig = px.imshow(
                            heatmap_values,
                            aspect="auto",
                            labels={
                                "x": "Samples",
                                "y": "Genes",
                                "color": "Z-score"
                            },
                            title=(
                                "Top Differentially Expressed "
                                "Genes Across Samples"
                            )
                        )

                        heatmap_fig.update_layout(
                            height=650
                        )

                        st.plotly_chart(
                            heatmap_fig,
                            use_container_width=True
                        )

    # ==================================================
    # TOP GENES TABLE
    # ==================================================

    st.subheader("🏆 Most Significant Genes")

    table_df = filtered.copy()

    if "padj" in table_df.columns:
        table_df = table_df.sort_values(
            "padj",
            ascending=True
        )

    display_columns = [
        c
        for c in [
            "gene_name",
            "baseMean",
            "log2FoldChange",
            "pvalue",
            "padj",
            "direction",
        ]
        if c in table_df.columns
    ]

    # Format a display-only copy so the underlying DE results
    # retain their original numerical precision.
    display_df = table_df[display_columns].head(50).copy()

    if "baseMean" in display_df.columns:
        display_df["baseMean"] = (
            pd.to_numeric(
                display_df["baseMean"],
                errors="coerce"
            ).map(
                lambda x: f"{x:,.3f}"
                if pd.notna(x)
                else ""
            )
        )

    if "log2FoldChange" in display_df.columns:
        display_df["log2FoldChange"] = (
            pd.to_numeric(
                display_df["log2FoldChange"],
                errors="coerce"
            ).map(
                lambda x: f"{x:.3f}"
                if pd.notna(x)
                else ""
            )
        )

    for column in ["pvalue", "padj"]:
        if column in display_df.columns:
            display_df[column] = (
                pd.to_numeric(
                    display_df[column],
                    errors="coerce"
                ).map(
                    lambda x: (
                        f"{x:.3e}"
                        if pd.notna(x) and x != 0
                        else "0"
                        if pd.notna(x)
                        else ""
                    )
                )
            )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # ==================================================
    # DOWNLOAD
    # ==================================================

    st.subheader("📥 Download Results")

    csv = filtered.to_csv(
        index=False
    ).encode("utf-8")

    download_name = (
        "filtered_DEG_results.csv"
        if is_customer_analysis
        else "LUAD_filtered_DEG_results.csv"
    )

    st.download_button(
        label="📥 Download Filtered DEG Results",
        data=csv,
        file_name=download_name,
        mime="text/csv",
    )
