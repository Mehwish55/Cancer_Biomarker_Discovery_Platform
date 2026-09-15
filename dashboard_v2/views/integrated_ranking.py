import streamlit as st
import pandas as pd
import plotly.express as px

from core.customer_ranking import calculate_customer_integrated_ranking


def _show_customer_integrated_ranking(customer_context):
    """Display integrated ranking calculated from the uploaded dataset."""

    st.title("🏆 Integrated Biomarker Ranking")

    st.markdown(
        f"""
        Explore the integrated evidence-based ranking of biomarkers
        identified from the uploaded dataset.

        **Comparison:** {customer_context.comparison}

        The ranking integrates differential-expression, ROC/AUC,
        machine-learning, stability, and functional-biology evidence
        calculated from this analysis.
        """
    )

    st.info(
        "Evidence from this analysis is used for this ranking. "
        "Reference LUAD results are not mixed into the analysis."
    )

    st.divider()

    # ==================================================
    # CUSTOMER RESULTS
    # ==================================================

    deg = customer_context.differential_expression

    if deg is None or deg.empty:
        st.warning(
            "Differential-expression results are not available."
        )
        return

    # --------------------------------------------------
    # ROC
    # --------------------------------------------------

    roc_results = st.session_state.get(
        "onconexa_customer_roc_results"
    )

    roc_analysis_id = st.session_state.get(
        "onconexa_customer_roc_analysis_id"
    )

    if (
        roc_results is None
        or roc_results.empty
        or roc_analysis_id != customer_context.analysis_id
    ):
        try:
            from core.customer_roc import calculate_customer_roc

            roc_results = calculate_customer_roc(
                expression=customer_context.expression_data,
                metadata=customer_context.metadata,
                candidates=deg,
                gene_column=customer_context.gene_column or "Gene",
            )

            st.session_state[
                "onconexa_customer_roc_results"
            ] = roc_results

            st.session_state[
                "onconexa_customer_roc_analysis_id"
            ] = customer_context.analysis_id

        except Exception as exc:
            st.warning(
                f"ROC evidence could not be calculated: {exc}"
            )
            roc_results = None

    # --------------------------------------------------
    # ML
    # --------------------------------------------------

    ml_results = st.session_state.get(
        "onconexa_customer_ml_results"
    )

    ml_analysis_id = st.session_state.get(
        "onconexa_customer_ml_analysis_id"
    )

    if ml_analysis_id != customer_context.analysis_id:
        ml_results = None

    # --------------------------------------------------
    # STABILITY
    # --------------------------------------------------

    stability_results = st.session_state.get(
        "onconexa_customer_stability_results"
    )

    stability_analysis_id = st.session_state.get(
        "onconexa_customer_stability_analysis_id"
    )

    if stability_analysis_id != customer_context.analysis_id:
        stability_results = None

    # --------------------------------------------------
    # PATHWAY
    # --------------------------------------------------

    pathway_cache = st.session_state.get(
        "onconexa_customer_pathway_cache"
    )

    pathway_results = None

    if (
        pathway_cache is not None
        and pathway_cache.get("analysis_id")
        == customer_context.analysis_id
    ):
        pathway_results = pathway_cache.get("result")

    # ==================================================
    # CALCULATE INTEGRATED RANKING
    # ==================================================

    try:
        ranking = calculate_customer_integrated_ranking(
            differential_expression=deg,
            roc_results=roc_results,
            ml_results=ml_results,
            stability_results=stability_results,
            pathway_results=pathway_results,
        )
    except Exception as exc:
        st.error(
            f"Integrated ranking could not be calculated: {exc}"
        )
        return

    if ranking is None or ranking.empty:
        st.warning(
            "No biomarker candidates could be ranked from the "
            "available evidence."
        )
        return

    # ==================================================
    # EVIDENCE STATUS
    # ==================================================

    available_components = ["Differential Expression"]

    if roc_results is not None and not roc_results.empty:
        available_components.append("ROC/AUC")

    if ml_results is not None:
        available_components.append("Machine Learning")

    if stability_results is not None:
        available_components.append("Stability")

    if pathway_results is not None:
        pathway_available = any(
            isinstance(pathway_results.get(key), pd.DataFrame)
            and not pathway_results.get(key).empty
            for key in ["BP", "CC", "MF"]
        )

        if pathway_available:
            available_components.append("Functional Biology")

    st.caption(
        "Evidence included: "
        + ", ".join(available_components)
    )

    # ==================================================
    # SUMMARY
    # ==================================================

    st.subheader("📊 Ranking Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Candidate Biomarkers",
            len(ranking),
        )

    with col2:
        if "integrated_score" in ranking.columns:
            st.metric(
                "Highest Integrated Score",
                f"{ranking['integrated_score'].max():.3f}",
            )
        else:
            st.metric(
                "Highest Integrated Score",
                "N/A",
            )

    with col3:
        if "integrated_rank" in ranking.columns:
            st.metric(
                "Best Rank",
                int(ranking["integrated_rank"].min()),
            )
        else:
            st.metric(
                "Best Rank",
                "N/A",
            )

    with col4:
        if "AUC" in ranking.columns and ranking["AUC"].notna().any():
            st.metric(
                "Best ROC-AUC",
                f"{ranking['AUC'].max():.3f}",
            )
        else:
            st.metric(
                "Best ROC-AUC",
                "N/A",
            )

    st.divider()

    # ==================================================
    # TOP BIOMARKERS
    # ==================================================

    st.subheader("🥇 Top Ranked Biomarkers")

    display_df = ranking.copy()

    if "integrated_rank" in display_df.columns:
        display_df = display_df.sort_values(
            "integrated_rank",
            ascending=True,
        )

    max_top = min(40, len(display_df))

    if max_top >= 5:
        top_n = st.slider(
            "Number of biomarkers to display",
            min_value=5,
            max_value=max_top,
            value=min(15, max_top),
            step=5,
        )
    else:
        top_n = max_top

    top_df = display_df.head(top_n)

    columns = [
        "integrated_rank",
        "gene_name",
        "integrated_score",
        "score_DE",
        "score_ROC",
        "score_AUC",
        "score_sensitivity",
        "score_specificity",
        "score_ML",
        "score_stability",
        "score_pathway",
        "AUC",
        "sensitivity",
        "specificity",
        "importance",
        "ML_rank",
    ]

    columns = [
        column
        for column in columns
        if column in top_df.columns
    ]

    st.dataframe(
        top_df[columns],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ==================================================
    # INTEGRATED SCORE
    # ==================================================

    st.subheader("📈 Integrated Evidence Score")

    if (
        "integrated_score" in display_df.columns
        and "gene_name" in display_df.columns
    ):
        fig = px.bar(
            top_df.sort_values(
                "integrated_score",
                ascending=True,
            ),
            x="integrated_score",
            y="gene_name",
            orientation="h",
            title="Integrated Biomarker Evidence Score",
            hover_data=[
                column
                for column in [
                    "integrated_rank",
                    "score_DE",
                    "score_ROC",
                    "score_ML",
                    "score_stability",
                    "score_pathway",
                    "AUC",
                ]
                if column in top_df.columns
            ],
        )

        fig.update_layout(
            height=max(500, top_n * 35),
            yaxis_title="Biomarker",
            xaxis_title="Integrated Score",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.divider()

    # ==================================================
    # INDIVIDUAL BIOMARKER
    # ==================================================

    st.subheader("🔎 Explore Individual Biomarker")

    if "gene_name" in display_df.columns:

        genes = (
            display_df["gene_name"]
            .dropna()
            .astype(str)
            .tolist()
        )

        selected_gene = st.selectbox(
            "Select biomarker",
            genes,
            key="customer_integrated_ranking_gene",
        )

        selected_rows = display_df[
            display_df["gene_name"].astype(str)
            == selected_gene
        ]

        if not selected_rows.empty:

            selected = selected_rows.iloc[0]

            st.markdown(
                f"### 🧬 {selected_gene}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                if "integrated_rank" in selected:
                    st.metric(
                        "Integrated Rank",
                        int(selected["integrated_rank"]),
                    )

            with col2:
                if "integrated_score" in selected:
                    st.metric(
                        "Integrated Score",
                        f"{float(selected['integrated_score']):.3f}",
                    )

            with col3:
                if (
                    "AUC" in selected
                    and pd.notna(selected["AUC"])
                ):
                    st.metric(
                        "ROC-AUC",
                        f"{float(selected['AUC']):.3f}",
                    )

            score_columns = [
                "score_DE",
                "score_ROC",
                "score_AUC",
                "score_sensitivity",
                "score_specificity",
                "score_ML",
                "score_stability",
                "score_pathway",
            ]

            available_scores = [
                column
                for column in score_columns
                if column in selected.index
                and pd.notna(selected[column])
            ]

            if available_scores:

                score_data = pd.DataFrame(
                    {
                        "Evidence Component": [
                            column.replace(
                                "score_",
                                "",
                            ).replace(
                                "_",
                                " ",
                            ).title()
                            for column in available_scores
                        ],
                        "Score": [
                            float(selected[column])
                            for column in available_scores
                        ],
                    }
                )

                fig = px.bar(
                    score_data,
                    x="Evidence Component",
                    y="Score",
                    title=f"Evidence Components — {selected_gene}",
                )

                fig.update_layout(
                    height=400,
                    xaxis_title="",
                    yaxis_title="Score",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

                st.dataframe(
                    score_data,
                    use_container_width=True,
                    hide_index=True,
                )

    st.divider()

    # ==================================================
    # METHODOLOGY
    # ==================================================

    st.subheader("🧠 How the Integrated Ranking Works")

    st.markdown(
        """
        The integrated ranking combines available evidence
        calculated from the uploaded dataset.

        **Evidence weighting**

        - Differential-expression evidence — **20%**
        - ROC/AUC discrimination — **30%**
        - Machine-learning evidence — **15%**
        - Biomarker stability — **20%**
        - Functional biology / pathway evidence — **15%**

        If an evidence component is unavailable, its weight is
        automatically redistributed across the available components.

        **Important:** This ranking is an evidence-integration tool.
        It does not represent clinical validation or a diagnostic claim.
        """
    )


def _show_static_integrated_ranking(data):
    """Display the existing LUAD reference/demo ranking."""

    st.title("🏆 Integrated Biomarker Ranking")

    st.markdown(
        """
        Explore the final evidence-based ranking of LUAD biomarker
        candidates generated by the existing reference analysis.

        The integrated score shown here is the existing pipeline
        output and is not recalculated.
        """
    )

    st.info(
        "This is the reference/demo analysis. "
        "Upload a dataset through New Analysis to generate "
        "an integrated biomarker ranking."
    )

    st.divider()

    ranking = data.get("integrated_ranking")

    if ranking is None or ranking.empty:
        st.error(
            "Integrated biomarker ranking data could not be loaded."
        )
        return

    st.subheader("📊 Ranking Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Candidate Biomarkers", len(ranking))

    with col2:
        if "integrated_score" in ranking.columns:
            best_score = ranking["integrated_score"].max()
            st.metric(
                "Highest Integrated Score",
                f"{best_score:.3f}",
            )
        else:
            st.metric(
                "Highest Integrated Score",
                "N/A",
            )

    with col3:
        if "integrated_rank" in ranking.columns:
            best_rank = ranking["integrated_rank"].min()
            st.metric(
                "Best Rank",
                int(best_rank),
            )
        else:
            st.metric(
                "Best Rank",
                "N/A",
            )

    with col4:
        if "AUC" in ranking.columns:
            best_auc = ranking["AUC"].max()
            st.metric(
                "Best ROC-AUC",
                f"{best_auc:.3f}",
            )
        else:
            st.metric(
                "Best ROC-AUC",
                "N/A",
            )

    st.divider()

    st.subheader("🥇 Top Ranked Biomarkers")

    display_df = ranking.copy()

    if "integrated_rank" in display_df.columns:
        display_df = display_df.sort_values(
            "integrated_rank",
            ascending=True,
        )

    top_n = st.slider(
        "Number of biomarkers to display",
        min_value=5,
        max_value=min(40, len(display_df)),
        value=min(15, len(display_df)),
        step=5,
    )

    top_df = display_df.head(top_n)

    columns = [
        "integrated_rank",
        "gene_name",
        "integrated_score",
        "score_AUC",
        "score_sensitivity",
        "score_specificity",
        "score_stability",
        "score_ML",
        "score_DE",
        "AUC",
    ]

    columns = [
        column
        for column in columns
        if column in top_df.columns
    ]

    st.dataframe(
        top_df[columns],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("📈 Integrated Score Distribution")

    if "integrated_score" in display_df.columns:

        fig = px.bar(
            top_df.sort_values(
                "integrated_score",
                ascending=True,
            ),
            x="integrated_score",
            y="gene_name",
            orientation="h",
            title="Integrated Evidence Score",
            hover_data=[
                column
                for column in [
                    "integrated_rank",
                    "AUC",
                    "score_AUC",
                    "score_sensitivity",
                    "score_specificity",
                    "score_stability",
                    "score_ML",
                    "score_DE",
                ]
                if column in top_df.columns
            ],
        )

        fig.update_layout(
            height=max(500, top_n * 35),
            yaxis_title="Biomarker",
            xaxis_title="Integrated Score",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.divider()

    st.subheader("🔎 Explore Individual Biomarker")

    if "gene_name" in display_df.columns:

        genes = display_df["gene_name"].dropna().tolist()

        selected_gene = st.selectbox(
            "Select biomarker",
            genes,
            key="static_integrated_ranking_gene",
        )

        selected = display_df[
            display_df["gene_name"] == selected_gene
        ].iloc[0]

        st.markdown(
            f"### 🧬 {selected_gene}"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if "integrated_rank" in selected:
                st.metric(
                    "Integrated Rank",
                    int(selected["integrated_rank"]),
                )

        with col2:
            if "integrated_score" in selected:
                st.metric(
                    "Integrated Score",
                    f"{selected['integrated_score']:.3f}",
                )

        with col3:
            if "AUC" in selected:
                st.metric(
                    "ROC-AUC",
                    f"{selected['AUC']:.3f}",
                )

        score_columns = [
            "score_AUC",
            "score_sensitivity",
            "score_specificity",
            "score_stability",
            "score_ML",
            "score_DE",
        ]

        available_scores = [
            column
            for column in score_columns
            if column in selected.index
        ]

        if available_scores:

            score_data = pd.DataFrame(
                {
                    "Evidence Component": [
                        column.replace(
                            "score_",
                            "",
                        ).replace(
                            "_",
                            " ",
                        ).title()
                        for column in available_scores
                    ],
                    "Score": [
                        selected[column]
                        for column in available_scores
                    ],
                }
            )

            fig = px.bar(
                score_data,
                x="Evidence Component",
                y="Score",
                title=f"Evidence Components — {selected_gene}",
            )

            fig.update_layout(
                height=400,
                xaxis_title="",
                yaxis_title="Score",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.dataframe(
                score_data,
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    st.subheader("🧠 Reference Ranking Methodology")

    st.info(
        """
        The reference ranking combines six existing evidence components:

        • ROC/AUC performance
        • Sensitivity
        • Specificity
        • Biomarker stability
        • Machine-learning evidence
        • Differential-expression evidence

        The reference ranking is not recalculated by this interface.
        """
    )

    st.divider()

    st.caption(
        "Source: results/final/"
        "LUAD_integrated_biomarker_ranking.csv"
    )


def show_integrated_ranking(data):
    """Show customer ranking when an analysis is active; otherwise demo ranking."""

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    if (
        customer_context is not None
        and customer_context.has_differential_expression()
    ):
        _show_customer_integrated_ranking(customer_context)
        return

    _show_static_integrated_ranking(data)
