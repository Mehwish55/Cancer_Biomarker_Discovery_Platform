import streamlit as st
import plotly.express as px

from core.customer_stability import run_customer_stability


def _show_customer_stability(customer_context):
    """Display stability evidence for the uploaded analysis."""

    st.title("🔬 Biomarker Stability Analysis")

    cancer_type = (
        str(customer_context.cancer_type).strip()
        if customer_context.cancer_type
        else "the uploaded dataset"
    )

    comparison = (
        str(customer_context.comparison).strip()
        if customer_context.comparison
        else "Group comparison"
    )

    st.markdown(
        f"""
        Evaluate the consistency and reproducibility of biomarker
        prioritization for **{cancer_type}**.

        **Comparison:** {comparison}

        Stability is calculated from repeated within-dataset
        resampling of the uploaded expression data.
        """
    )

    st.divider()

    cached_result = st.session_state.get(
        "onconexa_customer_stability_results"
    )
    cached_analysis_id = st.session_state.get(
        "onconexa_customer_stability_analysis_id"
    )

    try:
        if (
            cached_result is not None
            and cached_analysis_id == customer_context.analysis_id
        ):
            result = cached_result
        else:
            with st.spinner(
                "Running biomarker stability analysis..."
            ):
                result = run_customer_stability(
                    expression_data=customer_context.expression_data,
                    metadata=customer_context.metadata,
                    differential_expression=(
                        customer_context.differential_expression
                    ),
                    gene_column=customer_context.gene_column,
                    sample_columns=customer_context.sample_columns,
                    n_iterations=50,
                    random_state=42,
                )

            st.session_state[
                "onconexa_customer_stability_results"
            ] = result
            st.session_state[
                "onconexa_customer_stability_analysis_id"
            ] = customer_context.analysis_id

    except Exception as exc:
        st.error(
            f"Stability analysis could not be completed: {exc}"
        )
        return

    stability = result["stability"]

    st.header("📊 Stability Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Biomarkers Evaluated",
            result["n_features"],
        )

    with col2:
        st.metric(
            "Resampling Iterations",
            result["n_iterations"],
        )

    with col3:
        st.metric(
            "Highest Stability",
            f"{stability['stability_score'].max():.3f}",
        )

    with col4:
        st.metric(
            "Stable ≥0.80",
            int(
                (
                    stability["stability_score"] >= 0.80
                ).sum()
            ),
        )

    st.caption(
        f"Reference group: {result['reference_group']} · "
        f"Positive group: {result['positive_group']}"
    )

    st.divider()

    st.header("🏆 Stability Ranking")

    max_genes = min(40, len(stability))

    if max_genes >= 5:
        default_top_n = min(15, max_genes)

        top_n = st.slider(
            "Number of biomarkers to display",
            min_value=5,
            max_value=max_genes,
            value=default_top_n,
            step=5,
            key="customer_stability_top_n",
        )
    else:
        top_n = max_genes

    ranking_df = (
        stability
        .sort_values(
            "stability_score",
            ascending=False,
        )
        .head(top_n)
        .sort_values(
            "stability_score",
            ascending=True,
        )
    )

    fig_stability = px.bar(
        ranking_df,
        x="stability_score",
        y="gene_name",
        orientation="h",
        labels={
            "stability_score": "Stability Score",
            "gene_name": "Gene",
        },
        title="Most Stable Biomarker Candidates",
        hover_data=[
            c
            for c in [
                "mean_rf_importance",
                "sd_rf_importance",
                "rf_importance_consistency",
                "rank_consistency",
                "top10_stability",
                "top20_stability",
            ]
            if c in ranking_df.columns
        ],
    )

    fig_stability.update_layout(
        height=max(450, top_n * 28),
        yaxis={
            "categoryorder": "total ascending"
        },
    )

    st.plotly_chart(
        fig_stability,
        use_container_width=True,
    )

    st.divider()

    st.header("📋 Stability Results")

    st.markdown(
        """
        The table reports repeated-resampling stability measurements
        generated from the uploaded expression dataset.
        """
    )

    st.dataframe(
        stability,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.header("🧠 How to Interpret Stability")

    st.markdown(
        """
        **What does stability mean?**

        A stable biomarker remains consistently important across
        repeated resampling analyses of the evaluated dataset.

        **Higher stability**

        A higher stability score indicates more consistent
        model-based prioritization under the resampling procedure.

        **Why is stability useful?**

        A biomarker can show differential expression or strong
        discrimination while still being sensitive to sampling
        variation. Stability provides an additional
        reproducibility-oriented evidence layer.

        **Important limitation**

        This stability analysis is based on the uploaded dataset.
        It is not independent validation, clinical validation,
        or evidence of biological causality.

        Stability should therefore be interpreted together with
        differential expression, ROC/AUC, machine learning,
        independent validation where available, and biological
        evidence.
        """
    )

    st.divider()

    csv_data = stability.to_csv(index=False).encode("utf-8")

    safe_cancer_type = (
        str(customer_context.cancer_type).strip()
        if customer_context.cancer_type
        else "onconexa"
    )

    safe_cancer_type = (
        safe_cancer_type
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    st.download_button(
        "📥 Download Stability Results",
        data=csv_data,
        file_name=f"{safe_cancer_type}_stability_results.csv",
        mime="text/csv",
    )


def show_stability(data):

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    if (
        customer_context is not None
        and customer_context.has_differential_expression()
    ):
        _show_customer_stability(customer_context)
        return

    """
    Biomarker stability analysis page.

    Uses the existing V1 biomarker_stability.csv output.
    V2 only visualizes and interprets the existing results.
    """

    stability = data.get("stability")
    ranking = data.get("integrated_ranking")
    top15 = data.get("top15")

    # ==================================================
    # PAGE HEADER
    # ==================================================

    st.title("🔬 Biomarker Stability Analysis")

    st.markdown(
        """
        This section evaluates the consistency of biomarker
        selection across repeated resampling or bootstrap
        analyses performed by the underlying pipeline.

        Stability provides an additional layer of evidence
        beyond differential expression, validation, ROC/AUC,
        and machine learning.
        """
    )

    st.divider()

    # ==================================================
    # DATA CHECK
    # ==================================================

    if stability is None or stability.empty:

        st.error(
            "Biomarker stability results could not be loaded."
        )
        return

    # ==================================================
    # COLUMN DETECTION
    # ==================================================

    gene_column = None

    for candidate in [
        "gene_name",
        "gene",
        "Gene",
    ]:
        if candidate in stability.columns:
            gene_column = candidate
            break

    if gene_column is None:

        st.error(
            "The stability dataset does not contain a gene identifier column."
        )
        return

    # ==================================================
    # STABILITY SCORE DETECTION
    # ==================================================

    stability_score_column = None

    for candidate in [
        "stability_score",
        "stability",
        "Stability",
        "mean_stability",
    ]:
        if candidate in stability.columns:
            stability_score_column = candidate
            break

    # ==================================================
    # OVERVIEW METRICS
    # ==================================================

    st.header("📊 Stability Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Biomarkers Evaluated",
            len(stability),
        )

    with col2:

        if stability_score_column is not None:

            best_score = stability[
                stability_score_column
            ].max()

            st.metric(
                "Highest Stability",
                f"{best_score:.3f}",
            )

        else:

            st.metric(
                "Highest Stability",
                "N/A",
            )

    with col3:

        if stability_score_column is not None:

            mean_score = stability[
                stability_score_column
            ].mean()

            st.metric(
                "Mean Stability",
                f"{mean_score:.3f}",
            )

        else:

            st.metric(
                "Mean Stability",
                "N/A",
            )

    with col4:

        if stability_score_column is not None:

            stable_count = (
                stability[
                    stability_score_column
                ] >= 0.80
            ).sum()

            st.metric(
                "Highly Stable ≥0.80",
                int(stable_count),
            )

        else:

            st.metric(
                "Highly Stable ≥0.80",
                "N/A",
            )

    st.divider()

    # ==================================================
    # RAW STABILITY TABLE
    # ==================================================

    st.header("📋 Biomarker Stability Results")

    st.markdown(
        """
        The table below contains the stability measurements
        generated by the underlying biomarker analysis pipeline.
        """
    )

    st.dataframe(
        stability,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # ==================================================
    # STABILITY RANKING
    # ==================================================

    if stability_score_column is not None:

        st.header("🏆 Stability Ranking")

        max_genes = min(
            40,
            len(stability),
        )

        top_n = st.slider(
            "Number of biomarkers to display",
            min_value=5,
            max_value=max_genes,
            value=min(15, max_genes),
            step=5,
            key="stability_top_n",
        )

        ranking_df = (
            stability
            .sort_values(
                stability_score_column,
                ascending=False,
            )
            .head(top_n)
            .sort_values(
                stability_score_column,
                ascending=True,
            )
        )

        fig_stability = px.bar(
            ranking_df,
            x=stability_score_column,
            y=gene_column,
            orientation="h",
            labels={
                stability_score_column:
                    "Stability Score",
                gene_column:
                    "Gene",
            },
            title=(
                "Most Stable Biomarker Candidates"
            ),
            hover_data=[
                c
                for c in [
                    "ML_rank",
                    "integrated_rank",
                ]
                if c in ranking_df.columns
            ],
        )

        fig_stability.update_layout(
            height=max(
                450,
                top_n * 28,
            ),
            yaxis={
                "categoryorder":
                    "total ascending"
            },
        )

        st.plotly_chart(
            fig_stability,
            use_container_width=True,
        )

    # ==================================================
    # STABILITY VS INTEGRATED RANKING
    # ==================================================

    st.divider()

    st.header(
        "🔗 Stability vs Integrated Biomarker Ranking"
    )

    if (
        ranking is not None
        and not ranking.empty
        and stability_score_column is not None
    ):

        if (
            "gene_name" in ranking.columns
            and "integrated_rank" in ranking.columns
        ):

            stability_merge = stability[
                [
                    gene_column,
                    stability_score_column,
                ]
            ].copy()

            stability_merge = stability_merge.rename(
                columns={
                    gene_column:
                        "gene_name"
                }
            )

            if "integrated_score" in ranking.columns:

                comparison = ranking[
                    [
                        "gene_name",
                        "integrated_rank",
                        "integrated_score",
                    ]
                ].merge(
                    stability_merge,
                    on="gene_name",
                    how="inner",
                )

            else:

                comparison = ranking[
                    [
                        "gene_name",
                        "integrated_rank",
                    ]
                ].merge(
                    stability_merge,
                    on="gene_name",
                    how="inner",
                )

            if not comparison.empty:

                st.markdown(
                    """
                    This comparison shows whether biomarkers that
                    rank highly in the integrated evidence framework
                    also demonstrate strong stability.
                    """
                )

                fig_comparison = px.scatter(
                    comparison,
                    x="integrated_rank",
                    y=stability_score_column,
                    text="gene_name",
                    hover_name="gene_name",
                    labels={
                        "integrated_rank":
                            "Integrated Rank",
                        stability_score_column:
                            "Stability Score",
                    },
                    title=(
                        "Integrated Ranking vs Biomarker Stability"
                    ),
                )

                fig_comparison.update_traces(
                    textposition="top center"
                )

                fig_comparison.update_layout(
                    height=600
                )

                st.plotly_chart(
                    fig_comparison,
                    use_container_width=True,
                )

                st.dataframe(
                    comparison.sort_values(
                        "integrated_rank"
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No matching genes were found between "
                    "the stability and integrated ranking datasets."
                )

        else:

            st.info(
                "Integrated ranking does not contain the "
                "required columns."
            )

    else:

        st.info(
            "Integrated ranking or stability score information "
            "is not available."
        )

    # ==================================================
    # TOP BIOMARKERS
    # ==================================================

    st.divider()

    st.header(
        "🏆 Stability of Top Biomarker Candidates"
    )

    if (
        top15 is not None
        and not top15.empty
        and stability_score_column is not None
    ):

        if "gene_name" in top15.columns:

            top_stability = top15[
                ["gene_name"]
            ].merge(
                stability[
                    [
                        gene_column,
                        stability_score_column,
                    ]
                ].rename(
                    columns={
                        gene_column:
                            "gene_name"
                    }
                ),
                on="gene_name",
                how="left",
            )

            if "validation_rank" in top15.columns:

                top_stability = top_stability.merge(
                    top15[
                        [
                            "gene_name",
                            "validation_rank",
                        ]
                    ],
                    on="gene_name",
                    how="left",
                )

            top_stability = top_stability.sort_values(
                stability_score_column,
                ascending=False,
            )

            st.dataframe(
                top_stability,
                use_container_width=True,
                hide_index=True,
            )

    # ==================================================
    # INTERPRETATION
    # ==================================================

    st.divider()

    st.header(
        "🧠 How to Interpret Stability"
    )

    st.markdown(
        """
        **What does stability mean?**

        A stable biomarker remains consistently selected or
        important across repeated resampling analyses.

        **Higher stability**

        A higher stability score indicates more consistent
        biomarker selection under the resampling procedure
        used by the underlying pipeline.

        **Why is stability useful?**

        A biomarker with strong differential expression but
        poor stability may be sensitive to sampling variation.
        Strong stability provides additional evidence that the
        biomarker's prioritization is reproducible within the
        evaluated dataset.

        **How should it be used?**

        Stability should not be interpreted independently.
        It should be considered together with differential
        expression, independent validation, ROC/AUC,
        machine learning, and biological pathway evidence.

        **Important:** Stability does not establish clinical
        validity or biological causality. It is an additional
        reproducibility-oriented evidence layer.
        """
    )
