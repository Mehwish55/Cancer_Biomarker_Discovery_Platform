import streamlit as st
import plotly.express as px


def show_machine_learning(data):
    """
    Machine Learning evidence page.

    Uses existing V1 ML outputs:
    - model_comparison
    - rf_importance
    - integrated_ranking
    - top15
    """

    model_comparison = data.get("model_comparison")
    rf_importance = data.get("rf_importance")
    ranking = data.get("integrated_ranking")
    top15 = data.get("top15")

    # ==================================================
    # PAGE HEADER
    # ==================================================

    st.title("🤖 Machine Learning Evidence")

    st.markdown(
        """
        This section evaluates the contribution of machine learning
        to biomarker prioritization using the existing validated
        pipeline outputs.

        The analysis includes model-level performance and
        gene-level Random Forest feature importance.
        """
    )

    st.divider()

    # ==================================================
    # DATA AVAILABILITY
    # ==================================================

    if (
        model_comparison is None
        and rf_importance is None
    ):
        st.error(
            "Machine learning results could not be loaded."
        )
        return

    # ==================================================
    # MODEL COMPARISON
    # ==================================================

    st.header("📊 Model Performance")

    if (
        model_comparison is not None
        and not model_comparison.empty
    ):

        st.markdown(
            """
            Comparison of the machine learning models evaluated
            during biomarker validation.
            """
        )

        # Display available columns
        display_columns = [
            c
            for c in [
                "model",
                "Model",
                "AUC_mean",
                "AUC_std",
                "accuracy_mean",
                "accuracy_std",
                "precision_mean",
                "precision_std",
                "recall_mean",
                "recall_std",
                "f1_mean",
                "f1_std",
            ]
            if c in model_comparison.columns
        ]

        if display_columns:
            st.dataframe(
                model_comparison[display_columns],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(
                model_comparison,
                use_container_width=True,
                hide_index=True,
            )

        # --------------------------------------------------
        # AUC COLUMN DETECTION
        # --------------------------------------------------

        auc_column = None

        for candidate in [
            "AUC_mean",
            "auc_mean",
            "AUC",
            "auc",
        ]:
            if candidate in model_comparison.columns:
                auc_column = candidate
                break

        model_column = None

        for candidate in [
            "model",
            "Model",
            "algorithm",
        ]:
            if candidate in model_comparison.columns:
                model_column = candidate
                break

        # --------------------------------------------------
        # MODEL AUC VISUALIZATION
        # --------------------------------------------------

        if (
            auc_column is not None
            and model_column is not None
        ):

            st.subheader("🏆 Model ROC-AUC Comparison")

            fig_model = px.bar(
                model_comparison,
                x=model_column,
                y=auc_column,
                text_auto=".3f",
                labels={
                    model_column: "Model",
                    auc_column: "ROC-AUC",
                },
                title="Machine Learning Model Performance",
            )

            fig_model.update_layout(
                height=450,
                yaxis=dict(
                    range=[
                        max(
                            0,
                            float(
                                model_comparison[
                                    auc_column
                                ].min()
                            )
                            - 0.05,
                        ),
                        1.0,
                    ]
                ),
            )

            st.plotly_chart(
                fig_model,
                use_container_width=True,
            )

    else:

        st.warning(
            "Model comparison results are not available."
        )

    st.divider()

    # ==================================================
    # RANDOM FOREST FEATURE IMPORTANCE
    # ==================================================

    st.header("🌲 Random Forest Feature Importance")

    if (
        rf_importance is None
        or rf_importance.empty
    ):

        st.warning(
            "Random Forest feature importance results "
            "are not available."
        )

    else:

        st.markdown(
            """
            Random Forest feature importance indicates how strongly
            individual genes contributed to the machine learning model.
            Higher importance indicates greater contribution to the
            model's predictions.
            """
        )

        # --------------------------------------------------
        # IDENTIFY COLUMNS
        # --------------------------------------------------

        gene_column = None

        for candidate in [
            "gene_name",
            "gene",
            "Gene",
        ]:
            if candidate in rf_importance.columns:
                gene_column = candidate
                break

        importance_column = None

        for candidate in [
            "importance",
            "feature_importance",
            "Importance",
        ]:
            if candidate in rf_importance.columns:
                importance_column = candidate
                break

        rank_column = None

        for candidate in [
            "ML_rank",
            "ml_rank",
            "rank",
            "Rank",
        ]:
            if candidate in rf_importance.columns:
                rank_column = candidate
                break

        # --------------------------------------------------
        # RAW TABLE
        # --------------------------------------------------

        st.subheader("🧬 Gene-Level ML Evidence")

        st.dataframe(
            rf_importance,
            use_container_width=True,
            hide_index=True,
        )

        # --------------------------------------------------
        # TOP N SELECTOR
        # --------------------------------------------------

        if (
            gene_column is not None
            and importance_column is not None
        ):

            max_genes = min(
                40,
                len(rf_importance),
            )

            top_n = st.slider(
                "Number of genes to display",
                min_value=5,
                max_value=max_genes,
                value=min(15, max_genes),
                step=5,
            )

            plot_df = rf_importance.sort_values(
                importance_column,
                ascending=False,
            ).head(top_n)

            plot_df = plot_df.sort_values(
                importance_column,
                ascending=True,
            )

            # --------------------------------------------------
            # FEATURE IMPORTANCE CHART
            # --------------------------------------------------

            st.subheader(
                f"🏆 Top {top_n} ML Biomarkers"
            )

            fig_importance = px.bar(
                plot_df,
                x=importance_column,
                y=gene_column,
                orientation="h",
                labels={
                    importance_column:
                        "Feature Importance",
                    gene_column:
                        "Gene",
                },
                title=(
                    "Random Forest Feature Importance "
                    f"— Top {top_n} Genes"
                ),
                hover_data=[
                    c
                    for c in [
                        rank_column
                    ]
                    if c is not None
                ],
            )

            fig_importance.update_layout(
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
                fig_importance,
                use_container_width=True,
            )

    st.divider()

    # ==================================================
    # ML VS INTEGRATED RANKING
    # ==================================================

    st.header("🔗 ML Contribution to Integrated Ranking")

    if (
        ranking is not None
        and not ranking.empty
    ):

        required_columns = [
            "gene_name",
            "ML_rank",
            "integrated_rank",
        ]

        available = [
            c
            for c in required_columns
            if c in ranking.columns
        ]

        if len(available) == 3:

            comparison_df = ranking[
                available
            ].copy()

            comparison_df = comparison_df.sort_values(
                "integrated_rank"
            )

            st.markdown(
                """
                The table below shows how the machine learning
                ranking relates to the final integrated biomarker
                ranking.
                """
            )

            st.dataframe(
                comparison_df,
                use_container_width=True,
                hide_index=True,
            )

            # --------------------------------------------------
            # SCATTER PLOT
            # --------------------------------------------------

            st.subheader(
                "📈 ML Rank vs Integrated Rank"
            )

            fig_rank = px.scatter(
                comparison_df,
                x="ML_rank",
                y="integrated_rank",
                text="gene_name",
                hover_name="gene_name",
                labels={
                    "ML_rank":
                        "Random Forest ML Rank",
                    "integrated_rank":
                        "Integrated Biomarker Rank",
                },
                title=(
                    "Relationship Between ML Ranking "
                    "and Integrated Ranking"
                ),
            )

            fig_rank.update_traces(
                textposition="top center"
            )

            fig_rank.update_layout(
                height=600
            )

            st.plotly_chart(
                fig_rank,
                use_container_width=True,
            )

        else:

            st.info(
                "Integrated ranking does not contain the "
                "required ML ranking columns."
            )

    else:

        st.warning(
            "Integrated ranking data is not available."
        )

    st.divider()

    # ==================================================
    # TOP BIOMARKERS — ML EVIDENCE
    # ==================================================

    st.header("🏆 Top Biomarkers — ML Evidence")

    if (
        top15 is not None
        and not top15.empty
    ):

        ml_columns = [
            c
            for c in [
                "gene_name",
                "ML_rank",
                "AUC",
                "stability_score",
                "integrated_score",
                "integrated_rank",
            ]
            if c in top15.columns
        ]

        if ml_columns:

            ml_table = top15[
                ml_columns
            ].copy()

            if "ML_rank" in ml_table.columns:

                ml_table = ml_table.sort_values(
                    "ML_rank"
                )

            st.dataframe(
                ml_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "ML-related columns are not available "
                "in the top biomarker table."
            )

    else:

        st.warning(
            "Top biomarker data is not available."
        )

    # ==================================================
    # INTERPRETATION
    # ==================================================

    st.divider()

    st.header("🧠 How to Interpret the ML Evidence")

    st.markdown(
        """
        **Model performance**

        Higher ROC-AUC indicates stronger ability of the model
        to distinguish the evaluated classes.

        **Random Forest feature importance**

        Genes with higher feature importance contributed more
        strongly to the Random Forest model.

        **ML ranking**

        A lower ML rank represents a stronger position within
        the machine-learning-based prioritization.

        **Integrated ranking**

        ML evidence is one component of the existing integrated
        biomarker ranking. It should therefore be interpreted
        together with differential expression, independent
        validation, ROC/AUC, and stability evidence.

        **Important:** Machine learning evidence alone does not
        establish biological causality or clinical utility.
        It is one layer of evidence supporting biomarker
        prioritization.
        """
    )
