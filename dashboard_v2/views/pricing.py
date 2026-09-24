import streamlit as st


def show_pricing():

    st.title("💼 Pricing & Services")

    st.markdown(
        """
        ## OncoNexa Cancer Biomarker Analysis

        **From molecular data to evidence-supported biomarker candidates.**

        OncoNexa provides research-focused computational analysis
        for cancer biomarker discovery and validation.
        """
    )

    st.divider()

    # ==================================================
    # EXPLORE ONCONEXA
    # ==================================================

    st.subheader("🆓 Explore OncoNexa")

    st.markdown("### €0")

    st.markdown(
        """
        Explore the OncoNexa biomarker discovery workflow using
        a preloaded reference dataset.

        **Includes**
        - Preloaded reference analysis
        - Biomarker discovery workflow
        - Example validation results
        - Interactive visualizations
        """
    )

    st.divider()

    # ==================================================
    # PAID SERVICES
    # ==================================================

    st.subheader("🔬 Research Analysis Services")

    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("## Essential")
            st.markdown("### €200")
            st.caption("Initial biomarker discovery")

            st.markdown(
                """
                **Includes**
                - Differential expression
                - Biomarker candidate discovery
                - Basic ROC/AUC analysis
                - Pathway analysis
                - Results tables
                - Summary report
                """
            )

            st.markdown(
                '<div style="height: 24px;"></div>',
                unsafe_allow_html=True,
            )

            if st.button(
                "Request Essential Analysis",
                key="pricing_essential",
                use_container_width=True,
            ):
                st.session_state["pricing_request"] = "Essential"

    with col2:
        with st.container(border=True):
            st.markdown("## ⭐ Advanced")
            st.markdown("### €500")
            st.caption("Complete biomarker discovery & validation")

            st.markdown(
                """
                **Includes everything in Essential, plus**
                - ROC/AUC validation
                - Machine learning
                - Stability analysis
                - Evidence integration
                - Integrated biomarker ranking
                - Professional PDF report
                """
            )

            st.markdown(
                '<div style="height: 24px;"></div>',
                unsafe_allow_html=True,
            )

            if st.button(
                "Request Advanced Analysis",
                key="pricing_advanced",
                use_container_width=True,
            ):
                st.session_state["pricing_request"] = "Advanced"

    with col3:
        with st.container(border=True):
            st.markdown("## 🧬 Custom Research")
            st.markdown("### From €1,000")
            st.caption("Complex or customized projects")

            st.markdown(
                """
                **Suitable for**
                - Large datasets
                - Multiple comparisons
                - Custom workflows
                - Additional validation
                - Research-specific analysis
                - Customized reporting
                """
            )

            st.markdown(
                '<div style="height: 24px;"></div>',
                unsafe_allow_html=True,
            )

            if st.button(
                "Request Custom Analysis",
                key="pricing_custom",
                use_container_width=True,
            ):
                st.session_state["pricing_request"] = "Custom Research"

    if st.session_state.get("pricing_request"):
        st.divider()

        selected_package = st.session_state["pricing_request"]

        st.subheader(f"📩 Request {selected_package}")

        st.markdown(
            "Tell us about your project and dataset. "
            "We will review your requirements and determine the appropriate workflow."
        )

        with st.form("onconexa_analysis_request_form"):
            name = st.text_input("Name *")
            organization = st.text_input("Organization")
            email = st.text_input("Email *")

            col_a, col_b = st.columns(2)

            with col_a:
                data_type = st.selectbox(
                    "Data type",
                    [
                        "Bulk RNA-seq / Gene Expression",
                        "Single-cell RNA-seq",
                        "Proteomics",
                        "Genomics / Variant Data",
                        "Multi-omics",
                        "Other",
                    ],
                )

            with col_b:
                dataset_size = st.text_input(
                    "Dataset size",
                    placeholder="e.g. 500 samples × 20,000 genes",
                )

            cancer_type = st.text_input(
                "Cancer / disease area",
                placeholder="e.g. lung cancer, breast cancer",
            )

            project_description = st.text_area(
                "Project description *",
                placeholder=(
                    "Briefly describe your research question, "
                    "dataset and the analysis you need."
                ),
                height=140,
            )

            submitted = st.form_submit_button(
                "Submit Analysis Request",
                use_container_width=True,
            )

        if submitted:
            if not name.strip() or not email.strip() or not project_description.strip():
                st.error(
                    "Please complete all required fields marked with *."
                )
            else:
                st.success(
                    f"Your {selected_package} inquiry has been submitted successfully."
                )
                st.info(
                    "Thank you. Your project requirements have been captured "
                    "for review of the appropriate OncoNexa analysis workflow."
                )

    st.divider()

    # ==================================================
    # FUTURE SERVICES
    # ==================================================

    st.subheader("🚀 Expanding Analysis Capabilities")

    st.markdown(
        """
        OncoNexa is being expanded to support additional molecular
        data types and biomarker workflows.

        | Analysis | Availability |
        |---|---|
        | Bulk RNA-seq / Gene Expression | **Available** |
        | Single-cell RNA-seq | Coming next |
        | Proteomics | Planned |
        | Genomics / Variant Analysis | Planned |
        | Multi-omics Biomarker Discovery | Planned |

        Pricing for advanced data types will depend on dataset
        complexity and analysis requirements.
        """
    )

    st.divider()

    # ==================================================
    # HOW IT WORKS
    # ==================================================

    st.subheader("📋 How the Analysis Service Works")

    steps = [
        ("01", "Submit your data", "Provide your molecular dataset and available metadata."),
        ("02", "Data assessment", "We assess the dataset and determine the appropriate analysis workflow."),
        ("03", "Computational analysis", "OncoNexa performs biomarker discovery, validation and biological analysis."),
        ("04", "Results", "You receive analysis tables, figures and a professional report."),
    ]

    for number, title, description in steps:
        st.markdown(
            f"""
            **{number} — {title}**

            {description}
            """
        )

    st.info(
        "Need a customized biomarker analysis? Custom research projects "
        "are available from €1,000."
    )
