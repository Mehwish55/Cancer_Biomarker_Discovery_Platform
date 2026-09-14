import streamlit as st
import pandas as pd

from core.user_data import validate_user_data


def show_data_upload():
    st.title("🚀 New Analysis")
    st.write(
        "Upload your own cancer expression data and sample metadata "
        "to prepare a new biomarker analysis."
    )

    st.info(
        "For the first commercial version, OncoNexa supports an expression "
        "matrix plus a sample metadata file."
    )

    st.subheader("1. Upload Expression Data")

    expression_file = st.file_uploader(
        "Expression matrix (CSV)",
        type=["csv"],
        key="expression_upload",
        help="Upload genes × samples or long-format gene/sample/expression data.",
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
            st.error(f"Could not read expression file: {exc}")

    st.subheader("2. Upload Sample Metadata")

    metadata_file = st.file_uploader(
        "Sample metadata (CSV)",
        type=["csv"],
        key="metadata_upload",
        help="Metadata should contain sample_id and group information.",
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

            with st.expander("Preview metadata"):
                st.dataframe(
                    metadata_df.head(10),
                    use_container_width=True,
                )

        except Exception as exc:
            st.error(f"Could not read metadata file: {exc}")

    if expression_df is not None and metadata_df is not None:
        st.divider()
        st.subheader("3. Validate Data")

        validation = validate_user_data(
            expression_df,
            metadata_df,
        )

        if validation.is_valid:
            st.success("✅ Data validation passed")

            metrics = validation.metrics

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Expression rows",
                    f"{metrics.get('expression_rows', 0):,}",
                )

            with col2:
                st.metric(
                    "Samples",
                    f"{metrics.get('matched_samples', 0):,}",
                )

            with col3:
                st.metric(
                    "Groups",
                    f"{metrics.get('groups', 0):,}",
                )

            with col4:
                st.metric(
                    "Format",
                    metrics.get("expression_format", "Unknown"),
                )

            groups = metrics.get("group_labels", [])

            if groups:
                st.write("**Groups detected:**")
                st.write(", ".join(map(str, groups)))

            if validation.warnings:
                st.warning("⚠️ Validation warnings")

                for warning in validation.warnings:
                    st.write(f"- {warning}")

            st.divider()

            st.success(
                "🎯 Your data is ready for the next analysis step."
            )

            st.caption(
                "Differential expression, candidate discovery, ROC/AUC, "
                "machine learning, stability, pathway analysis, and "
                "integrated ranking will be connected to this upload "
                "workflow in the next stage."
            )

        else:
            st.error("❌ Data validation failed")

            for message in validation.messages:
                st.write(f"- {message}")

            if validation.warnings:
                st.warning("⚠️ Additional warnings")

                for warning in validation.warnings:
                    st.write(f"- {warning}")
