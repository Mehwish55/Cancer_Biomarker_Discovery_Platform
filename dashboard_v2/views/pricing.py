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
    # FREE DEMO
    # ==================================================

    st.subheader("🆓 Free Demo")

    st.markdown("### €0")

    st.markdown(
        """
        Explore the OncoNexa biomarker discovery workflow using
        an example cancer dataset.

        **Includes**
        - Example LUAD dataset
        - Biomarker discovery workflow
        - Example validation results
        - Example visualizations
        """
    )

    st.divider()

    # ==================================================
    # PAID SERVICES
    # ==================================================

    st.subheader("🔬 Research Analysis Services")

    col1, col2, col3 = st.columns(3)

    with col1:
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

        st.button(
            "Request Essential Analysis",
            key="pricing_essential",
            disabled=True,
        )

    with col2:
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

        st.button(
            "Request Advanced Analysis",
            key="pricing_advanced",
            disabled=True,
        )

    with col3:
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

        st.button(
            "Request Custom Analysis",
            key="pricing_custom",
            disabled=True,
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
