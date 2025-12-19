



import os
import base64
import streamlit as st
from PyPDF2 import PdfReader
from databricks.databricks_trigger import run_job_and_get_gdrive_link
from databricks.payload import payload_setter
from dotenv import load_dotenv

load_dotenv()



# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Consumption Estimate Calculator",
    layout="wide",
    initial_sidebar_state="expanded"
)



st.markdown(
        """
            <style>
                    div.stButton > button {
                                background-color: #D7263D !important;
                                            color: #ffffff !important;
                                                        border: none !important;
                                                                }
                                                                    </style>
                                                                        """,
                                                                            unsafe_allow_html=True
                                                                            )





# ======================================================
# PLACEHOLDER LLM FUNCTION
# ======================================================
def query_llm(prompt):
    if "connection success" in prompt.lower():
        return "Connection success"
    return {"resources": [], "assumptions": []}

# ======================================================
# BACKEND STATE INITIALIZATION
# ======================================================
if "data_migration_store" not in st.session_state:
    st.session_state.data_migration_store = {}

if "ml_store" not in st.session_state:
    st.session_state.ml_store = {}

if "reporting_store" not in st.session_state:
    st.session_state.reporting_store = {}

if "llm_store" not in st.session_state:
        st.session_state.llm_store = {}


if "final_prompt" not in st.session_state:
    st.session_state.final_prompt = ""


if "gdrive_link" not in st.session_state:
    st.session_state.gdrive_link = None


# ======================================================
# LOAD CSS
# ======================================================
def load_css():
    if os.path.exists("style.css"):
        with open("style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ======================================================
# FIXED BRANDING
# ======================================================
def get_base64_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_image("./assets/sigmoid-logo.jpeg")

# ======================================================
# HERO
# ======================================================
st.markdown(
    """
    <div class="hero-section">
        <h1 class="hero-title">Consumption Estimate Calculator</h1>
        <p class="hero-subtitle-strong">An AI-powered calculator</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ======================================================
# SIDEBAR
# ======================================================
with st.sidebar:
    logo_base64 = get_base64_image("./assets/sigmoid-logo.jpeg")

    st.markdown(
        f"""
        <div class="sidebar-logo">
            <img src="data:image/png;base64,{logo_base64}" class="sidebar-logo">
            <p class="sidebar-text">Powered by <span class="db-red">Databricks</span></p>
        </div>
        <hr class="sidebar-divider">
        """,
        unsafe_allow_html=True
    )

    st.header("User Input")

    client_name = st.text_input(
        "Client Name",
        placeholder="Acme Corp"
    )

    use_case_name = st.text_input(
        "Use Case Name",
        placeholder="Annual Budget Planning"
    )

    # =========================
    # BUDGET
    # =========================
    st.subheader("Budget")

    annual_budget = st.number_input(
        "Annual Cloud Budget (USD)",
        min_value=0,
        value=0,
        step=10000
    )


    # =========================
    # MARKET CONFIG
    # =========================
    st.subheader("Market Configuration")
    number_of_markets = st.number_input("Number of Markets", min_value=0, value=0)

    markets = []
    for i in range(int(number_of_markets)):
        markets.append({
            "market": f"M{i+1}",
            "multiplier": st.number_input(
                f"Consumption Multiplier (M{i+1})",
                min_value=0.0, value=0.0, step=0.1, key=f"m_mult_{i}"
            ),
            "start_month": st.selectbox(
                f"Market Entry Month (M{i+1})",
                list(range(1, 13)), key=f"m_month_{i}"
            )
        })

    use_case_type = st.selectbox(
        "Use Case Type",
        ["Select use case", "Data Migration", "Machine Learning", "Reporting", "LLM"]
    )

    cloud_options = ["Databricks", "AWS", "Azure"]

    # =========================
    # DATA MIGRATION
    # =========================
    if use_case_type == "Data Migration":
        dm = st.session_state.data_migration_store
        st.subheader("Data Migration Inputs")

        dm["cloud_type"] = st.multiselect("Cloud Type", cloud_options, default=[])

        dm["migration_type"] = st.radio(
            "Migration Type",
            ["One-time Historical Load", "Ongoing Incremental", "Both"]
        )

        dm["pipeline_mode"] = st.radio(
            "Pipeline Mode", ["Batch", "Streaming"]
        )

        dm["historical_data_gb"] = st.number_input(
            "Historical Data Size (GB)", min_value=0, value=0
        )
        dm["daily_incremental_gb"] = st.number_input(
            "Daily Incremental Data (GB/day)", min_value=0, value=0
        )
        dm["pipelines"] = st.number_input(
            "Number of Pipelines", min_value=0, value=0
        )
        dm["runs_per_day"] = st.number_input(
            "Pipeline Runs per Day", min_value=0, value=0
        )
        dm["avg_runtime_hours"] = st.number_input(
            "Avg Runtime per Pipeline (hours)", min_value=0.0, value=0.0
        )
        dm["source_systems"] = st.number_input(
            "Source Systems", min_value=0, value=0
        )
        dm["destination_systems"] = st.number_input(
            "Destination Systems", min_value=0, value=0
        )
        dm["transformation_complexity"] = st.selectbox(
            "Transformation Complexity",
            ["Low (Copy)", "Medium (Joins)", "High (Aggregations / Enrichment)"]
        )
        dm["concurrent_pipelines"] = st.number_input(
            "Max Concurrent Pipelines", min_value=0, value=0
        )
        dm["storage_retention_days"] = st.number_input(
            "Raw Data Retention (days)", min_value=0, value=0
        )

    # =========================
    # MACHINE LEARNING
    # =========================
    if use_case_type == "Machine Learning":
        ml = st.session_state.ml_store
        st.subheader("Machine Learning Inputs")

        ml["cloud_type"] = st.multiselect("Cloud Type", cloud_options, default=[])

        ml["workload_types"] = st.multiselect(
            "Workload Type",
            ["Training", "Batch Inference", "Real-time Inference"],
            default=[]
        )

        ml["training_data_gb"] = st.number_input(
            "Training Data Size (GB)", min_value=0, value=0
        )
        ml["training_frequency"] = st.selectbox(
            "Training Frequency",
            ["Daily", "Weekly", "Monthly", "On Demand"]
        )
        ml["avg_training_hours"] = st.number_input(
            "Avg Training Duration (hours)", min_value=0.0, value=0.0
        )
        ml["models_count"] = st.number_input(
            "Number of Models", min_value=0, value=0
        )
        ml["inference_requests_per_day"] = st.number_input(
            "Inference Requests per Day", min_value=0, value=0
        )
        ml["peak_concurrency"] = st.number_input(
            "Peak Concurrent Inference Requests", min_value=0, value=0
        )
        ml["use_gpu"] = st.radio("Use GPU?", ["No", "Yes"])
        ml["gpu_hours_per_day"] = (
            st.number_input("GPU Usage (hours/day)", min_value=0, value=0)
            if ml["use_gpu"] == "Yes" else 0
        )
        ml["model_retention_days"] = st.number_input(
            "Model Retention (days)", min_value=0, value=0
        )

    # =========================
    # REPORTING
    # =========================
    if use_case_type == "Reporting":
        rp = st.session_state.reporting_store
        st.subheader("Reporting Inputs")

        rp["cloud_type"] = st.multiselect("Cloud Type", cloud_options, default=[])

        rp["tool"] = st.selectbox("Reporting Tool", ["Power BI", "Tableau"])

        rp["user_type"] = st.radio("User Type", ["Viewer", "Pro", "Premium"])

        rp["number_of_users"] = st.number_input(
            "Number of Users", min_value=0, value=0
        )
    if use_case_type == "LLM":
            llm = st.session_state.llm_store
            st.subheader("LLM Inputs")
            llm["cloud_type"] = st.multiselect("Cloud Type", cloud_options, default=[])
            llm["llm_category"] = st.selectbox(
                "LLM Type",
                [
                    "Generative AI",
                    "Embedding / Vector Search",
                    "Fine-tuning",
                    "RAG (Retrieval Augmented Generation)"
                ]
            )
            llm["llm_model"] = st.selectbox(
                "LLM Model Version",
                [
                    "GPT-4.1",
                    "GPT-4o",
                     "GPT-4.0"
                ]
                                                                                
            )
            llm["requests_per_day"] = st.number_input(
                        "Requests per Day", min_value=0, value=0
                            )
            
                
     
                                                                                                                                                                                                                                                

# ======================================================
# UPLOAD ARTIFACTS
# ======================================================
import cloudinary
import cloudinary.uploader
import os
import asyncio
import streamlit as st
from PyPDF2 import PdfReader
from azure.storage.filedatalake import DataLakeServiceClient

# ------------------------------------------------------
# Cloudinary config
# ------------------------------------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# ------------------------------------------------------
# Async Cloudinary upload
# ------------------------------------------------------
async def upload_image_to_cloudinary_async(file):
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        file,
        resource_type="image"
    )
    return result["secure_url"]

from azure.storage.filedatalake import DataLakeServiceClient
import os

def upload_to_adls(uploaded_file, adls_path):
    account_name = os.getenv("AZURE_STORAGE_ACCOUNT")
    account_key = os.getenv("ACCOUNT_KEY")
    file_system = os.getenv("AZURE_BLOB_CONTAINER")

    if not all([account_name, account_key, file_system]):
        raise RuntimeError(
            f"Missing ADLS config. "
            f"AZURE_STORAGE_ACCOUNT={account_name}, "
            f"ACCOUNT_KEY={'SET' if account_key else None}, "
            f"ADLS_FILE_SYSTEM={file_system}"
        )

    service_client = DataLakeServiceClient(
        account_url=f"https://{account_name}.dfs.core.windows.net",
        credential=account_key
    )

    fs_client = service_client.get_file_system_client(file_system)
    file_client = fs_client.get_file_client(adls_path)

    uploaded_file.seek(0)
    file_client.upload_data(uploaded_file.read(), overwrite=True)

    # Return HTTPS blob URL (for downstream LLM)
    return f"https://{account_name}.blob.core.windows.net/{file_system}/{adls_path}"

# ------------------------------------------------------
# UI
# ------------------------------------------------------
st.header("Upload Artifacts")
st.info("Upload PNG, JPG, JPEG, or PDF files.")

uploaded_files = st.file_uploader(
    "Select files",
    accept_multiple_files=True,
    type=["png", "jpg", "jpeg", "pdf"]
)

# Session state to prevent re-upload
if "image_urls" not in st.session_state:
    st.session_state.image_urls = []

if "pdf_urls" not in st.session_state:
    st.session_state.pdf_urls = []

if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""

# ------------------------------------------------------
# Upload Button (IMPORTANT)
# ------------------------------------------------------
adls_urls = []
pdf_urls = []

if "image_urls" not in st.session_state:
    st.session_state.image_urls = []

if "pdf_urls" not in st.session_state:
    st.session_state.adls_urls = []

if st.button("Upload Files"):
    if not uploaded_files:
        st.warning("Please select files first.")
    else:
        with st.spinner("Uploading..."):
            for file in uploaded_files:
                if file.name.lower().endswith(".pdf"):
                    adls_path = f"uploads/pdfs/{file.name}"
                    pdf_url = upload_to_adls(file, adls_path)

                    st.session_state.pdf_urls.append(pdf_url)

                    st.success("PDF uploaded to ADLS")
                    st.code(pdf_url)

                else:
                    img_url = asyncio.run(
                        upload_image_to_cloudinary_async(file)
                    )

                    st.session_state.image_urls.append(img_url)

                    st.success("Image uploaded successfully!")
                    st.image(img_url, width=200)


# ======================================================
# AI ANALYSIS
# ======================================================
st.header("AI Analysis & Cost Estimation")

if st.button(
    "Finish Input & Copy to Prompt",
    type="primary",
    use_container_width=True
):
    st.session_state.final_prompt = f"""
DATA MIGRATION:
{st.session_state.data_migration_store}

MACHINE LEARNING:
{st.session_state.ml_store}

REPORTING:
{st.session_state.reporting_store}
""".strip()


prompt_input = st.text_area(
    "User Prompt",
    value=st.session_state.final_prompt or
    "Extract cloud resources and estimate consumption. Output JSON only.",
    height=260
)

st.markdown("---")
col1, col2 = st.columns([3, 1])

with col1:
    if st.button("Generate Cost Estimate with AI", type="primary", use_container_width=True):
        with st.spinner("Analyzing and estimating..."):
            payload = payload_setter(
                image_uris=st.session_state.image_urls,
                file_uris=st.session_state.pdf_urls,
                client_name=client_name,
                use_case_name=use_case_name,
                markets=markets,
                user_prompt=prompt_input,
                budget=annual_budget
            )

            try:
                gdrive_link = run_job_and_get_gdrive_link(payload)
            except Exception as e:
                st.error(f"Cost estimation failed: {str(e)}")
                st.stop()

            st.session_state.gdrive_link = gdrive_link


# if st.button("Generate Cost Estimate with AI",type="primary",use_container_width=True):
#      with st.spinner("Analyzing and estimating..."):
#                  payload = payload_setter(
#                      image_uris=st.session_state.image_urls,
#                      file_uris=st.session_state.pdf_urls,
#                      client_name=client_name,
#                      use_case_name=use_case_name,
#                      markets=markets,
#                      user_prompt=prompt_input,
#                      budget=annual_budget
#                     )
                 
#                     try:
#                        gdrive_link = run_job_and_get_gdrive_link(payload)
#                     except Exception as e:
#                         st.error(f"Cost estimation failed: {str(e)}")
#                         st.stop()

#                     st.session_state.gdrive_link = gdrive_link

                 
                 






if st.session_state.gdrive_link:
    st.markdown("---")
    st.link_button(
        "Open Result in Google Drive",
        st.session_state.gdrive_link,
        use_container_width=True
    )