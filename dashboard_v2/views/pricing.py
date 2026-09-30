import streamlit as st
import resend


def send_analysis_request(
    selected_package,
    name,
    organization,
    email,
    data_type,
    dataset_size,
    cancer_type,
    project_description,
):
    api_key = st.secrets["RESEND_API_KEY"]
    recipient = st.secrets["ONCONEXA_REQUEST_EMAIL"]

    resend.api_key = api_key

    params = {
        "from": "OncoNexa <onboarding@resend.dev>",
        "to": [recipient],
        "subject": f"OncoNexa Analysis Request — {selected_package}",
        "reply_to": email,
        "text": f"""
New OncoNexa analysis request

Package:
{selected_package}

Name:
{name}

Organization:
{organization or "Not provided"}

Customer email:
{email}

Data type:
{data_type}

Dataset size:
{dataset_size or "Not provided"}

Cancer / disease area:
{cancer_type or "Not provided"}

Project description:
{project_description}

Please review this request and contact the customer at:
{email}
""",
    }

    return resend.Emails.send(params)


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

    st.markdown(
        """
        <style>
        /* ==============================================
           PRICING SERVICE TYPOGRAPHY
           ============================================== */

        .service-title {
            font-size: 1.25rem;
            font-weight: 800;
            line-height: 1.25;
            color: #ffffff;
            margin-bottom: 6px;
        }

        .service-price {
            font-size: 1.15rem;
            font-weight: 800;
            line-height: 1.3;
            color: #ffffff;
            margin-bottom: 6px;
        }

        .service-description {
            font-size: 0.92rem;
            line-height: 1.5;
            color: #d0d0d0;
            opacity: 1;
        }

        .service-heading {
            font-size: 0.92rem;
            font-weight: 800;
            line-height: 1.4;
            color: #ffffff;
            margin-bottom: 7px;
        }

        .service-features {
            font-size: 0.92rem;
            font-weight: 400;
            line-height: 1.5;
            color: #d0d0d0;
        }

        /* ==============================================
           BLUE ANALYSIS BUTTONS
           ============================================== */

        div[data-testid="stButton"] button {
            background-color: #2563eb !important;
            color: #ffffff !important;
            border: 1px solid #2563eb !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            min-height: 46px !important;
        }

        div[data-testid="stButton"] button:hover {
            background-color: #1d4ed8 !important;
            border-color: #1d4ed8 !important;
            color: #ffffff !important;
        }

div[data-testid="stFormSubmitButton"] button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: 1px solid #2563eb !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    min-height: 46px !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background-color: #1d4ed8 !important;
    border-color: #1d4ed8 !important;
    color: #ffffff !important;
}

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ==================================================
        # SERVICE TABLE
    # Each service uses the same five-column structure for consistent alignment.

    # ESSENTIAL
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns(
            [0.55, 1.35, 1.15, 3.25, 1.45],
            gap="medium",
        )

        with col1:
            st.markdown(
                "<div style='font-size:1.45rem; padding-top:6px;'>🧪</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                '<div class="service-title">Essential</div>',
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                '<div class="service-price">€200</div>',
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                '<div class="service-description">'
                '<strong>Initial biomarker discovery</strong><br>'
                'Differential expression · Biomarker discovery · '
                'ROC/AUC · Pathway analysis · Results tables · Summary report'
                '</div>',
                unsafe_allow_html=True,
            )

        with col5:
            if st.button(
                "Request Essential",
                key="pricing_essential",
                width="stretch",
            ):
                st.session_state["pricing_request"] = "Essential"


    # ADVANCED
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns(
            [0.55, 1.35, 1.15, 3.25, 1.45],
            gap="medium",
        )

        with col1:
            st.markdown(
                "<div style='font-size:1.45rem; padding-top:6px;'>⭐</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                '<div class="service-title">Advanced</div>',
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                '<div class="service-price">€500</div>',
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                '<div class="service-description">'
                '<strong>Complete discovery &amp; validation</strong><br>'
                'ROC/AUC validation · Machine learning · Stability analysis · '
                'Evidence integration · Biomarker ranking · Professional PDF report'
                '</div>',
                unsafe_allow_html=True,
            )

        with col5:
            if st.button(
                "Request Advanced",
                key="pricing_advanced",
                width="stretch",
            ):
                st.session_state["pricing_request"] = "Advanced"


    # CUSTOM RESEARCH
    with st.container(border=True):
        col1, col2, col3, col4, col5 = st.columns(
            [0.55, 1.35, 1.15, 3.25, 1.45],
            gap="medium",
        )

        with col1:
            st.markdown(
                "<div style='font-size:1.45rem; padding-top:6px;'>🧬</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                '<div class="service-title">Custom Research</div>',
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                '<div class="service-price">From €1,000</div>',
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                '<div class="service-description">'
                '<strong>Complex or customized projects</strong><br>'
                'Large datasets · Multiple comparisons · Custom workflows · '
                'Additional validation · Research-specific analysis · Customized reporting'
                '</div>',
                unsafe_allow_html=True,
            )

        with col5:
            if st.button(
                "Request Custom",
                key="pricing_custom",
                width="stretch",
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
                try:
                    send_analysis_request(
                        selected_package=selected_package,
                        name=name,
                        organization=organization,
                        email=email,
                        data_type=data_type,
                        dataset_size=dataset_size,
                        cancer_type=cancer_type,
                        project_description=project_description,
                    )

                    st.success(
                        "Your analysis request has been submitted successfully."
                    )
                    st.info(
                        "Thank you. We will review your requirements and "
                        "contact you by email regarding the appropriate "
                        "OncoNexa analysis workflow."
                    )

                except Exception as e:
                    st.error(
                        "We could not submit your request at this time. "
                        "Please try again later."
                    )
                    st.caption(f"Technical details: {e}")

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
