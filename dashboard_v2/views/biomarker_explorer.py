import numpy as np
import pandas as pd
import streamlit as st

from core.evidence_engine import get_biomarker_evidence


def _fmt(value, digits=3):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _show_customer_biomarker_explorer(customer_context):
    st.title("🧬 Biomarker Explorer")

    st.markdown(
        f"""
        Explore candidate biomarkers identified from the uploaded
        **{customer_context.cancer_type}** dataset.

        **Comparison:** {customer_context.comparison}
        """
    )

    st.caption(
        "Customer-specific evidence is shown below. "
        "Reference LUAD evidence is not mixed into this analysis."
    )

    st.divider()

    deg = customer_context.differential_expression

    if deg is None or deg.empty:
        st.warning(
            "Differential-expression results are not available."
        )
        return

    if "gene" not in deg.columns:
        st.error(
            "Customer differential-expression results do not contain "
            "the expected gene column."
        )
        return

    genes = (
        deg["gene"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )

    if not genes:
        st.warning("No biomarker candidates are available.")
        return

    selected_gene = st.selectbox(
        "🔎 Select a biomarker",
        genes,
        key="customer_biomarker_explorer_gene",
    )

    selected_de = deg[
        deg["gene"].astype(str) == selected_gene
    ]

    if selected_de.empty:
        st.error(
            f"No differential-expression result was found for {selected_gene}."
        )
        return

    de_row = selected_de.iloc[0]

    expression = customer_context.expression_data
    metadata = customer_context.metadata

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
        from core.customer_roc import calculate_customer_roc

        try:
            roc_results = calculate_customer_roc(
                expression=expression,
                metadata=metadata,
                candidates=deg,
                gene_column=customer_context.gene_column or "Gene",
            )
            st.session_state[
                "onconexa_customer_roc_results"
            ] = roc_results
            st.session_state[
                "onconexa_customer_roc_analysis_id"
            ] = customer_context.analysis_id
        except Exception:
            roc_results = None

    roc_row = None

    if (
        roc_results is not None
        and not roc_results.empty
        and "gene_name" in roc_results.columns
    ):
        matches = roc_results[
            roc_results["gene_name"].astype(str) == selected_gene
        ]

        if not matches.empty:
            roc_row = matches.iloc[0]

    st.header(f"🔬 {selected_gene}")

    st.subheader("📈 ROC / Biomarker Discrimination")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "ROC-AUC",
            _fmt(roc_row["AUC"], 4)
            if roc_row is not None
            else "N/A",
        )

    with col2:
        st.metric(
            "Sensitivity",
            f"{float(roc_row['sensitivity']) * 100:.2f}%"
            if (
                roc_row is not None
                and pd.notna(roc_row["sensitivity"])
            )
            else "N/A",
        )

    with col3:
        st.metric(
            "Specificity",
            f"{float(roc_row['specificity']) * 100:.2f}%"
            if (
                roc_row is not None
                and pd.notna(roc_row["specificity"])
            )
            else "N/A",
        )

    if roc_row is not None:
        reference_group = roc_row.get(
            "reference_group"
        )
        positive_group = roc_row.get(
            "positive_group"
        )

        if reference_group and positive_group:
            st.caption(
                f"Reference group: {reference_group} | "
                f"Positive group: {positive_group}"
            )

    # ==================================================
    # CUSTOMER ROC CURVE
    # Presentation-layer visualization using the
    # uploaded expression data and customer metadata.
    # ==================================================
    if roc_row is not None:
        try:
            gene_column = customer_context.gene_column or "Gene"
            sample_column = "sample_id"
            group_column = "group"

            if (
                expression is not None
                and metadata is not None
                and gene_column in expression.columns
                and sample_column in metadata.columns
                and group_column in metadata.columns
            ):
                metadata_plot = metadata.copy()
                metadata_plot[sample_column] = (
                    metadata_plot[sample_column].astype(str)
                )
                metadata_plot[group_column] = (
                    metadata_plot[group_column].astype(str)
                )

                groups = (
                    metadata_plot[group_column]
                    .dropna()
                    .unique()
                    .tolist()
                )

                if len(groups) == 2:
                    reference_group = groups[0]
                    positive_group = groups[1]

                    sample_ids = metadata_plot[sample_column].tolist()

                    gene_matches = (
                        expression[gene_column].astype(str)
                        == selected_gene
                    )

                    if gene_matches.any():
                        gene_values = pd.to_numeric(
                            expression.loc[
                                gene_matches
                            ].iloc[0][sample_ids],
                            errors="coerce",
                        ).to_numpy(dtype=float)

                        y_true = (
                            metadata_plot[group_column]
                            == positive_group
                        ).astype(int).to_numpy()

                        valid = np.isfinite(gene_values)

                        y_valid = y_true[valid]
                        scores = gene_values[valid]

                        if (
                            len(scores) >= 4
                            and len(np.unique(y_valid)) == 2
                        ):
                            # Match the direction used by customer_roc.py.
                            auc_value = float(roc_row["AUC"])

                            if (
                                roc_row.get("direction")
                                == "Lower in positive group"
                            ):
                                scores = -scores

                            # Generate ROC points from the uploaded
                            # customer expression values.
                            thresholds = np.r_[
                                np.inf,
                                np.sort(
                                    np.unique(scores)
                                )[::-1],
                                -np.inf,
                            ]

                            tpr = []
                            fpr = []

                            positives = np.sum(y_valid == 1)
                            negatives = np.sum(y_valid == 0)

                            for threshold in thresholds:
                                predicted = scores >= threshold

                                tp = np.sum(
                                    (predicted == 1)
                                    & (y_valid == 1)
                                )
                                fp = np.sum(
                                    (predicted == 1)
                                    & (y_valid == 0)
                                )

                                tpr.append(
                                    tp / positives
                                    if positives
                                    else 0.0
                                )
                                fpr.append(
                                    fp / negatives
                                    if negatives
                                    else 0.0
                                )

                            roc_df = pd.DataFrame(
                                {
                                    "False Positive Rate": fpr,
                                    "True Positive Rate": tpr,
                                }
                            ).drop_duplicates()

                            st.markdown("### ROC Curve")

                            st.line_chart(
                                roc_df.set_index(
                                    "False Positive Rate"
                                ),
                                use_container_width=True,
                            )

                            st.caption(
                                f"ROC curve for {selected_gene}. "
                                f"AUC = {auc_value:.4f}. "
                                f"Reference: {reference_group} | "
                                f"Positive: {positive_group}"
                            )

                        else:
                            st.info(
                                "A ROC curve could not be generated "
                                "because insufficient valid expression "
                                "values were available."
                            )

        except Exception:
            st.info(
                "The ROC summary is available, but the ROC curve "
                "could not be generated for this biomarker."
            )

    # ==================================================
    # CUSTOMER BIOMARKER EXPRESSION DISTRIBUTION
    # ==================================================
    try:
        gene_column = customer_context.gene_column or "Gene"
        sample_column = "sample_id"
        group_column = "group"

        if (
            expression is not None
            and metadata is not None
            and gene_column in expression.columns
            and sample_column in metadata.columns
            and group_column in metadata.columns
        ):
            metadata_expression = metadata.copy()

            metadata_expression[sample_column] = (
                metadata_expression[sample_column].astype(str)
            )
            metadata_expression[group_column] = (
                metadata_expression[group_column].astype(str)
            )

            groups = (
                metadata_expression[group_column]
                .dropna()
                .unique()
                .tolist()
            )

            gene_matches = (
                expression[gene_column].astype(str)
                == selected_gene
            )

            if len(groups) == 2 and gene_matches.any():
                sample_ids = metadata_expression[sample_column].tolist()

                gene_values = pd.to_numeric(
                    expression.loc[
                        gene_matches
                    ].iloc[0][sample_ids],
                    errors="coerce",
                )

                expression_df = pd.DataFrame(
                    {
                        "Sample": sample_ids,
                        "Group": metadata_expression[
                            group_column
                        ].tolist(),
                        "Expression": gene_values.to_numpy(
                            dtype=float
                        ),
                    }
                )

                expression_df = expression_df.dropna(
                    subset=["Expression"]
                )

                if not expression_df.empty:
                    st.subheader(
                        "🧬 Biomarker Expression Distribution"
                    )

                    st.caption(
                        f"Expression of {selected_gene} across "
                        "the two customer-defined groups."
                    )

                    # Group-wise boxplot using Plotly.
                    import plotly.express as px

                    fig = px.box(
                        expression_df,
                        x="Group",
                        y="Expression",
                        points="all",
                        hover_data=["Sample"],
                        labels={
                            "Group": "Customer Group",
                            "Expression": (
                                f"{selected_gene} Expression"
                            ),
                        },
                    )

                    fig.update_layout(
                        height=450,
                        showlegend=False,
                        margin=dict(
                            l=20,
                            r=20,
                            t=30,
                            b=20,
                        ),
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                    )

                    # Compact group summary.
                    summary = (
                        expression_df
                        .groupby("Group")["Expression"]
                        .agg(
                            Samples="count",
                            Median="median",
                            Mean="mean",
                        )
                        .reset_index()
                    )

                    st.dataframe(
                        summary,
                        use_container_width=True,
                        hide_index=True,
                    )

    except Exception:
        st.info(
            "Expression distribution could not be generated "
            "for this biomarker."
        )

    # ==================================================
    # CUSTOMER CANDIDATE BIOMARKER RANKING
    # ==================================================
    try:
        ranking_columns = {
            "gene",
            "padj",
            "log2FoldChange",
        }

        if ranking_columns.issubset(deg.columns):
            ranking_df = deg[
                ["gene", "padj", "log2FoldChange"]
            ].copy()

            ranking_df["padj"] = pd.to_numeric(
                ranking_df["padj"],
                errors="coerce",
            )

            ranking_df["log2FoldChange"] = pd.to_numeric(
                ranking_df["log2FoldChange"],
                errors="coerce",
            )

            ranking_df = ranking_df.dropna(
                subset=[
                    "gene",
                    "padj",
                    "log2FoldChange",
                ]
            )

            ranking_df = ranking_df[
                ranking_df["padj"] > 0
            ]

            if not ranking_df.empty:
                ranking_df["-log10(padj)"] = (
                    -np.log10(ranking_df["padj"])
                )

                ranking_df = ranking_df.sort_values(
                    "-log10(padj)",
                    ascending=False,
                ).head(15)

                ranking_df = ranking_df.sort_values(
                    "-log10(padj)",
                    ascending=True,
                )

                st.subheader(
                    "🏆 Candidate Biomarker Ranking"
                )

                st.caption(
                    "Top candidate biomarkers ranked by "
                    "statistical significance. Bar length represents "
                    "-log10(adjusted p-value); direction is shown "
                    "by log2 fold change."
                )

                import plotly.express as px

                fig = px.bar(
                    ranking_df,
                    x="-log10(padj)",
                    y="gene",
                    orientation="h",
                    hover_data={
                        "log2FoldChange": ":.3f",
                        "padj": ".3e",
                        "-log10(padj)": ":.2f",
                    },
                    labels={
                        "-log10(padj)": "-log10(adjusted p-value)",
                        "gene": "Biomarker",
                        "log2FoldChange": "log2 fold change",
                        "padj": "Adjusted p-value",
                    },
                )

                fig.update_layout(
                    height=max(
                        420,
                        28 * len(ranking_df) + 120,
                    ),
                    margin=dict(
                        l=20,
                        r=20,
                        t=30,
                        b=20,
                    ),
                    showlegend=False,
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

    except Exception:
        st.info(
            "Candidate biomarker ranking could not be "
            "generated for this analysis."
        )

    st.divider()

    # ==================================================
    # CUSTOMER DIFFERENTIAL EXPRESSION EFFECT PLOT
    # ==================================================
    try:
        effect_columns = {
            "gene",
            "log2FoldChange",
            "padj",
        }

        if effect_columns.issubset(deg.columns):
            effect_df = deg[
                ["gene", "log2FoldChange", "padj"]
            ].copy()

            effect_df["log2FoldChange"] = pd.to_numeric(
                effect_df["log2FoldChange"],
                errors="coerce",
            )

            effect_df["padj"] = pd.to_numeric(
                effect_df["padj"],
                errors="coerce",
            )

            effect_df = effect_df.dropna(
                subset=[
                    "gene",
                    "log2FoldChange",
                    "padj",
                ]
            )

            effect_df = effect_df[
                effect_df["padj"] > 0
            ]

            if not effect_df.empty:
                effect_df["neg_log10_padj"] = (
                    -np.log10(effect_df["padj"])
                )

                effect_df["Biomarker"] = (
                    effect_df["gene"].astype(str)
                    == selected_gene
                ).map(
                    {
                        True: "Selected biomarker",
                        False: "Other DE genes",
                    }
                )

                st.subheader(
                    "📊 Differential Expression Effect"
                )

                st.caption(
                    "Differential-expression effect size and "
                    "statistical significance for the uploaded "
                    "customer dataset."
                )

                import plotly.express as px

                fig = px.scatter(
                    effect_df,
                    x="log2FoldChange",
                    y="neg_log10_padj",
                    hover_name="gene",
                    hover_data={
                        "log2FoldChange": ":.3f",
                        "padj": ".3e",
                        "neg_log10_padj": ":.2f",
                        "Biomarker": True,
                    },
                    labels={
                        "log2FoldChange": "log2 fold change",
                        "neg_log10_padj": (
                            "-log10(adjusted p-value)"
                        ),
                        "Biomarker": "Category",
                    },
                    color="Biomarker",
                )

                fig.add_vline(
                    x=0,
                    line_dash="dash",
                )

                fig.update_layout(
                    height=500,
                    margin=dict(
                        l=20,
                        r=20,
                        t=30,
                        b=20,
                    ),
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                )

    except Exception:
        st.info(
            "Differential-expression effect plot could not "
            "be generated for this analysis."
        )

    st.divider()

    st.subheader("🧬 Differential Expression")

    de_columns = [
        column
        for column in [
            "gene",
            "log2FoldChange",
            "pvalue",
            "padj",
            "direction",
        ]
        if column in de_row.index
    ]

    if de_columns:
        de_display = pd.DataFrame(
            [
                {
                    column: de_row[column]
                    for column in de_columns
                }
            ]
        )

        st.dataframe(
            de_display,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.subheader("📋 Biomarker Candidates")

    candidate_columns = [
        column
        for column in [
            "gene",
            "log2FoldChange",
            "pvalue",
            "padj",
            "direction",
        ]
        if column in deg.columns
    ]

    candidate_display = deg[candidate_columns].copy()

    if "padj" in candidate_display.columns:
        candidate_display = candidate_display.sort_values(
            "padj",
            ascending=True,
            na_position="last",
        )

    st.dataframe(
        candidate_display,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "ROC-AUC represents discriminatory performance within the "
        "uploaded dataset. It is not independent-cohort validation."
    )


def show_biomarker_explorer(data):

    customer_context = st.session_state.get(
        "onconexa_customer_context"
    )

    if (
        customer_context is not None
        and customer_context.has_differential_expression()
    ):
        _show_customer_biomarker_explorer(customer_context)
        return

    st.title("🧬 Biomarker Explorer")

    st.markdown(
        """
        Explore individual LUAD biomarker candidates across the
        evidence generated by the validated V1 biomarker pipeline.
        """
    )

    st.divider()

    # ==========================================================
    # DATA
    # ==========================================================

    top15 = data.get("top15")

    if top15 is None or top15.empty:
        st.warning("Top biomarker data could not be loaded.")
        return

    if "gene_name" not in top15.columns:
        st.error("The top biomarker dataset does not contain gene_name.")
        return

    genes = (
        top15["gene_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if not genes:
        st.warning("No biomarker genes are available.")
        return

    # ==========================================================
    # GENE SELECTION
    # ==========================================================

    selected_gene = st.selectbox(
        "🔎 Select a biomarker",
        genes,
        key="biomarker_explorer_gene_v2",
    )

    # ==========================================================
    # EVIDENCE ENGINE
    # ==========================================================

    evidence = get_biomarker_evidence(
        data,
        selected_gene,
    )

    if not evidence:
        st.error(
            f"No evidence could be retrieved for {selected_gene}."
        )
        return

    integrated = evidence.get(
        "integrated_ranking",
        {},
    )

    top = evidence.get(
        "top15",
        {},
    )

    roc = evidence.get(
        "roc_validation",
        {},
    )

    validation = evidence.get(
        "independent_validation",
        {},
    )

    ml = evidence.get(
        "machine_learning",
        {},
    )

    stability = evidence.get(
        "stability",
        {},
    )

    de = evidence.get(
        "differential_expression",
        {},
    )

    # ==========================================================
    # HEADER
    # ==========================================================

    st.header(f"🔬 {selected_gene}")

    st.caption(
        "Evidence retrieved from canonical V1-derived datasets."
    )

    # ==========================================================
    # KEY METRICS
    # ==========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        rank = integrated.get("integrated_rank")

        st.metric(
            "🏆 Integrated Rank",
            f"#{int(rank)}"
            if rank is not None
            else "N/A",
        )

    with col2:
        auc = roc.get("AUC")

        st.metric(
            "📈 ROC-AUC",
            _fmt(auc),
        )

    with col3:
        stability_score = stability.get(
            "stability_score"
        )

        st.metric(
            "🔬 Stability",
            _fmt(stability_score),
        )

    with col4:
        validation_rank = top.get(
            "validation_rank"
        )

        st.metric(
            "✅ Validation Rank",
            f"#{int(validation_rank)}"
            if validation_rank is not None
            else "N/A",
        )

    st.divider()

    # ==========================================================
    # EVIDENCE PROFILE
    # ==========================================================

    st.subheader("🧩 Evidence Profile")

    evidence_items = {
        "Integrated Ranking": integrated.get(
            "integrated_score"
        ),
        "ROC-AUC": roc.get("AUC"),
        "Sensitivity": roc.get(
            "sensitivity"
        ),
        "Specificity": roc.get(
            "specificity"
        ),
        "ML Evidence": integrated.get(
            "score_ML"
        ),
        "Stability": integrated.get(
            "score_stability"
        ),
        "DE Evidence": integrated.get(
            "score_DE"
        ),
    }

    profile_rows = []

    for label, value in evidence_items.items():

        if value is not None:

            try:
                numeric_value = float(value)

                profile_rows.append(
                    {
                        "Evidence": label,
                        "Score": numeric_value,
                    }
                )

            except (
                TypeError,
                ValueError,
            ):
                pass

    if profile_rows:

        profile_df = pd.DataFrame(
            profile_rows
        )

        st.dataframe(
            profile_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No numerical evidence profile is available."
        )

    st.divider()

    # ==========================================================
    # ROC / VALIDATION
    # ==========================================================

    st.subheader(
        "📈 ROC / Independent Validation"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "ROC-AUC",
            _fmt(
                roc.get("AUC"),
                4,
            ),
        )

    with col2:

        sensitivity = roc.get(
            "sensitivity"
        )

        st.metric(
            "Sensitivity",
            f"{float(sensitivity) * 100:.2f}%"
            if sensitivity is not None
            else "N/A",
        )

    with col3:

        specificity = roc.get(
            "specificity"
        )

        st.metric(
            "Specificity",
            f"{float(specificity) * 100:.2f}%"
            if specificity is not None
            else "N/A",
        )

    with col4:

        status = top.get(
            "validation_status"
        )

        st.metric(
            "Validation Status",
            status if status else "N/A",
        )

    # ==========================================================
    # INDEPENDENT VALIDATION
    # ==========================================================

    st.subheader(
        "🧪 Independent Validation Evidence"
    )

    validation_rows = []

    for key, value in validation.items():

        if value is not None:

            validation_rows.append(
                {
                    "Metric": key,
                    "Value": value,
                }
            )

    if validation_rows:

        st.dataframe(
            pd.DataFrame(validation_rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No independent-validation fields "
            "are available for this biomarker."
        )

    # ==========================================================
    # MACHINE LEARNING
    # ==========================================================

    st.subheader(
        "🤖 Machine Learning Evidence"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        ml_rank = ml.get(
            "ML_rank"
        )

        st.metric(
            "ML Rank",
            f"#{int(ml_rank)}"
            if ml_rank is not None
            else "N/A",
        )

    with col2:

        st.metric(
            "Feature Importance",
            _fmt(
                ml.get("importance"),
                4,
            ),
        )

    with col3:

        st.metric(
            "ML Evidence Score",
            _fmt(
                integrated.get(
                    "score_ML"
                ),
                3,
            ),
        )

    # ==========================================================
    # STABILITY
    # ==========================================================

    st.subheader("🔬 Biomarker Stability")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Stability Score",
            _fmt(
                stability.get("stability_score"),
                4,
            ),
        )

    with col2:
        stability_rank = stability.get("stability_rank")

        st.metric(
            "Stability Rank",
            f"#{int(stability_rank)}"
            if stability_rank is not None
            else "N/A",
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

    st.markdown("**Stability Evidence Components**")

    stability_items = {
        "Mean Random-Forest Importance":
            stability.get("mean_rf_importance"),

        "SD Random-Forest Importance":
            stability.get("sd_rf_importance"),

        "Mean Permutation Importance":
            stability.get("mean_permutation_importance"),

        "SD Permutation Importance":
            stability.get("sd_permutation_importance"),

        "Mean Random-Forest Rank":
            stability.get("mean_rf_rank"),

        "Mean Permutation Rank":
            stability.get("mean_permutation_rank"),

        "Top-10 Folds":
            stability.get("top10_folds"),

        "Top-20 Folds":
            stability.get("top20_folds"),

        "Normalized Random-Forest":
            stability.get("normalized_rf"),

        "Normalized Permutation":
            stability.get("normalized_permutation"),
    }

    stability_rows = []

    for label, value in stability_items.items():

        if value is not None:
            stability_rows.append(
                {
                    "Metric": label,
                    "Value": value,
                }
            )

    if stability_rows:
        st.dataframe(
            pd.DataFrame(stability_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No detailed stability evidence is available "
            "for this biomarker."
        )

    # ==========================================================
    # DIFFERENTIAL EXPRESSION
    # ==========================================================

    st.subheader(
        "🧬 Differential Expression"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        direction = de.get(
            "direction"
        )

        st.metric(
            "Direction",
            direction
            if direction
            else "N/A",
        )

    with col2:

        st.metric(
            "Base Mean",
            _fmt(
                de.get(
                    "baseMean"
                ),
                2,
            ),
        )

    with col3:

        st.metric(
            "log₂ Fold Change",
            _fmt(
                de.get(
                    "log2FoldChange"
                ),
                3,
            ),
        )

    with col4:

        st.metric(
            "Adjusted p-value",
            _fmt(
                de.get(
                    "padj"
                ),
                6,
            ),
        )

    # ==========================================================
    # INTEGRATED RANKING
    # ==========================================================

    st.subheader(
        "🏆 Official Integrated Ranking"
    )

    ranking_rows = [
        {
            "Component": "Integrated Score",
            "Value": integrated.get(
                "integrated_score"
            ),
        },
        {
            "Component": "Integrated Rank",
            "Value": integrated.get(
                "integrated_rank"
            ),
        },
        {
            "Component": "ROC/AUC",
            "Value": integrated.get(
                "score_AUC"
            ),
        },
        {
            "Component": "Sensitivity",
            "Value": integrated.get(
                "score_sensitivity"
            ),
        },
        {
            "Component": "Specificity",
            "Value": integrated.get(
                "score_specificity"
            ),
        },
        {
            "Component": "Stability",
            "Value": integrated.get(
                "score_stability"
            ),
        },
        {
            "Component": "Machine Learning",
            "Value": integrated.get(
                "score_ML"
            ),
        },
        {
            "Component": "Differential Expression",
            "Value": integrated.get(
                "score_DE"
            ),
        },
    ]

    ranking_rows = [
        row
        for row in ranking_rows
        if row["Value"] is not None
    ]

    if ranking_rows:

        st.dataframe(
            pd.DataFrame(
                ranking_rows
            ),
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "These values are retrieved from the existing V1-derived "
        "evidence. V2 does not recalculate or modify the official "
        "integrated ranking."
    )
