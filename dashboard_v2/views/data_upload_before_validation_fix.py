import re

import pandas as pd
import streamlit as st

from core.user_data import validate_user_data


def _find_gene_column(df):
    """Find the most likely gene identifier column."""
    preferred = [
        "gene",
        "gene_id",
        "gene_name",
        "symbol",
        "gene_symbol",
        "ensembl",
        "ensembl_id",
    ]

    lookup = {str(col).strip().lower(): col for col in df.columns}

    for name in preferred:
        if name in lookup:
            return lookup[name]

    return None


def _detect_sample_groups(columns):
    """
    Detect common experimental groups from sample names.

    Examples:
        Normal_01 -> Normal
        Tumor_01  -> Tumor
        Control1  -> Control
        Treat_01  -> Treat
    """
    detected = {}

    for column in columns:
        name = str(column).strip()

        # Remove common replicate/sample numbering.
        group = re.sub(
            r"([_\-\s]?(sample|rep|replicate)?[_\-\s]?\d+)$",
            "",
            name,
            flags=re.IGNORECASE,
        )

        # Also handle names such as Sample01.
        group = re.sub(
            r"\d+$",
            "",
            group,
            flags=re.IGNORECASE,
        )

        group = group.strip("_- ")

        if group:
            detected[column] = group

    return detected


def _expression_type(df, gene_column):
    """Provide a conservative estimate of expression data type."""
    numeric_columns = df.drop(columns=[gene_column], errors="ignore").select_dtypes(
        include="number"
    )

    if numeric_columns.empty:
        return "Unknown"

    values = numeric_columns.to_numpy().ravel()

    values = values[~pd.isna(values)]

    if len(values) == 0:
        return "Unknown"

    minimum = values.min()
    maximum = values.max()

    # Heuristic only. We deliberately do not claim certainty.
    if minimum >= 0 and maximum > 100:
        return "Possibly raw counts"

    if minimum >= 0 and maximum <= 100:
        return "Possibly normalized / transformed"

    return "Possibly transformed expression"


def _dataset_assessment(expression_df):
    """Assess a wide-format expression matrix."""
    gene_column = _find_gene_column(expression_df)

    if gene_column is None:
        return {
            "valid_structure": False,
            "gene_column": None,
            "sample_columns": [],
            "groups": {},
            "expression_type": "Unknown",
            "messages": [
                "Could not identify a gene identifier column."
            ],
        }

    sample_columns = [
        column
        for column in expression_df.columns
        if column != gene_column
    ]

    numeric_sample_columns = [
        column
        for column in sample_columns
        if pd.api.types.is_numeric_dtype(expression_df[column])
    ]

    group_map = _detect_sample_groups(numeric_sample_columns)

    group_names = sorted(set(group_map.values()))

    return {
        "valid_structure": len(numeric_sample_columns) >= 2,
        "gene_column": gene_column,
        "sample_columns": numeric_sample_columns,
        "groups": group_map,
        "group_names": group_names,
        "expression_type": _expression_type(
            expression_df,
            gene_column,
        ),
        "messages": [],
    }


def _show_assessment(expression_df):
    """Display automatic dataset assessment."""
    assessment = _dataset_assessment(expression_df)

    st.subheader("3. Dataset Assessment")

    if not assessment["valid_structure"]:
        st.error(
            "❌ OncoNexa could not identify a valid expression matrix."
        )

        for message in assessment["messages"]:
            st.write(f"- {message}")

        return False

    gene_column = assessment["gene_column"]
    sample_columns = assessment["sample_columns"]
    group_map = assessment["groups"]
    group_names = assessment["group_names"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Genes",
            f"{len(expression_df):,}",
        )

    with col2:
        st.metric(
            "Samples",
            f"{len(sample_columns):,}",
        )

    with col3:
        st.metric(
            "Groups",
            f"{len(group_names):,}",
        )

    with col4:
        st.metric(
            "Gene column",
            str(gene_column),
        )

    st.write(
        f"**Expression data type:** {assessment['expression_type']}"
    )

    if len(group_names) >= 2:
        st.success(
            "✅ Multiple experimental groups detected."
        )

        group_counts = {}

        for group in group_map.values():
            group_counts[group] = group_counts.get(group, 0) + 1

        group_table = pd.DataFrame(
            {
                "Group": list(group_counts.keys()),
                "Samples": list(group_counts.values()),
            }
        )

        st.dataframe(
            group_table,
            hide_index=True,
            use_container_width=True,
        )

        with st.expander("Detected sample groups"):
            for sample, group in group_map.items():
                st.write(f"- `{sample}` → **{group}**")

    elif len(group_names) == 1:
        st.warning(
            "⚠️ Only one experimental group was detected. "
            "A comparison-based biomarker analysis normally requires "
            "at least two groups."
        )

    else:
        st.warning(
            "⚠️ OncoNexa could not automatically determine experimental groups."
        )

    duplicate_genes = (
        expression_df[gene_column]
        .astype(str)
        .duplicated()
        .sum()
    )

    missing_values = int(
        expression_df[sample_columns].isna().sum().sum()
    )

    if duplicate_genes > 0:
        st.warning(
            f"⚠️ {duplicate_genes:,} duplicate gene identifiers detected."
        )
    else:
        st.success("✅ No duplicate gene identifiers detected.")

    if missing_values > 0:
        st.warning(
            f"⚠️ {missing_values:,} missing expression values detected."
        )
    else:
        st.success("✅ No missing expression values detected.")

    return True


def _show_configuration(expression_df):
    """Show analysis configuration after dataset assessment."""
    assessment = _dataset_assessment(expression_df)

    group_names = assessment["group_names"]

    st.divider()
    st.subheader("4. Configure Analysis")

    cancer_type = st.text_input(
        "Cancer type / disease",
        placeholder="e.g. Lung cancer, Breast cancer, Colorectal cancer",
        help="Used as contextual information for the analysis.",
    )

    if len(group_names) >= 2:
        comparison_options = [
            f"{group_names[0]} vs {group_names[1]}"
        ]

        if len(group_names) > 2:
            comparison_options.append(
                "Multi-group analysis"
            )

        comparison = st.selectbox(
            "Experimental comparison",
            comparison_options,
        )

    else:
        comparison = None

    analysis_type = st.selectbox(
        "Expression data type",
        [
            "Automatic detection",
            "Raw RNA-seq counts",
            "Normalized expression",
            "Log-transformed expression",
        ],
    )

    st.info(
        "OncoNexa will use these settings to select the appropriate "
        "analysis workflow. The existing LUAD demonstration remains "
        "separate from user-uploaded analyses."
    )

    ready = (
        len(group_names) >= 2
        and len(assessment["sample_columns"]) >= 4
    )

    if not ready:
        st.warning(
            "⚠️ Please provide a dataset with at least two groups "
            "and enough samples for comparative analysis."
        )
        return

    st.divider()

    st.subheader("5. Start Analysis")

    st.write(
        "Your dataset has passed the initial structural assessment. "
        "The next stage will run the disease-agnostic biomarker workflow."
    )

    run_analysis = st.button(
        "🚀 Run Analysis",
        type="primary",
        use_container_width=True,
    )

    if run_analysis:
        st.session_state["onconexa_analysis_requested"] = True
        st.session_state["onconexa_analysis_config"] = {
            "cancer_type": cancer_type,
            "comparison": comparison,
            "analysis_type": analysis_type,
            "gene_column": assessment["gene_column"],
            "sample_columns": assessment["sample_columns"],
            "groups": assessment["groups"],
        }

        st.success(
            "✅ Analysis configuration accepted."
        )

        st.info(
            "The analysis engine is the next development step. "
            "No biological results have been calculated yet."
        )


def show_data_upload():
    st.title("🚀 New Analysis")

    st.write(
        "Upload your own cancer expression data and prepare it "
        "for OncoNexa's biomarker discovery workflow."
    )

    st.info(
        "For the first commercial version, OncoNexa accepts an "
        "expression matrix and can detect common sample-group "
        "patterns automatically."
    )

    st.subheader("1. Upload Expression Data")

    expression_file = st.file_uploader(
        "Expression matrix (CSV)",
        type=["csv"],
        key="expression_upload",
        help=(
            "Preferred format: one gene per row and one sample "
            "per column. A gene identifier column is required."
        ),
    )

    expression_df = None

    if expression_file is not None:
        try:
            expression_df = pd.read_csv(expression_file)

            st.success(
                f"Expression data loaded: "
                f"{expression_df.shape[0]:,} rows × "
                f"{expression_df.shape[1]:,} columns"
            )

            with st.expander("Preview expression data"):
                st.dataframe(
                    expression_df.head(10),
                    use_container_width=True,
                )

        except Exception as exc:
            st.error(
                f"Could not read expression file: {exc}"
            )

    st.subheader("2. Optional Sample Metadata")

    metadata_file = st.file_uploader(
        "Sample metadata (CSV)",
        type=["csv"],
        key="metadata_upload",
        help=(
            "Optional when group information can be detected "
            "from sample names."
        ),
    )

    metadata_df = None

    if metadata_file is not None:
        try:
            metadata_df = pd.read_csv(metadata_file)

            st.success(
                f"Metadata loaded: "
                f"{metadata_df.shape[0]:,} rows × "
                f"{metadata_df.shape[1]:,} columns"
            )

            with st.expander("Preview sample metadata"):
                st.dataframe(
                    metadata_df.head(10),
                    use_container_width=True,
                )

        except Exception as exc:
            st.error(
                f"Could not read metadata file: {exc}"
            )

    if expression_df is not None:

        # If metadata is supplied, run the existing validator first.
        if metadata_df is not None:
            validation = validate_user_data(
                expression_df,
                metadata_df,
            )

            if not validation.is_valid:
                st.error("❌ Metadata / expression validation failed.")

                for message in validation.messages:
                    st.write(f"- {message}")

                return

            if validation.warnings:
                for warning in validation.warnings:
                    st.warning(f"⚠️ {warning}")

        assessment_ok = _show_assessment(
            expression_df
        )

        if assessment_ok:
            _show_configuration(
                expression_df
            )
