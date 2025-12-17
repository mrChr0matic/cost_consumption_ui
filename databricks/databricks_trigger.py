import os
import json
import time
import requests
from azure.storage.blob import BlobServiceClient
# from databricks.sdk.runtime import dbutils


# ------------------------------------------------------------
# ENV
# ------------------------------------------------------------

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


DATABRICKS_WORKSPACE_URL = require_env("DATABRICKS_WORKSPACE_URL")
DATABRICKS_TOKEN = require_env("DATABRICKS_TOKEN")
DATABRICKS_JOB_ID = require_env("DATABRICKS_JOB_ID")

AZURE_STORAGE_ACCOUNT = require_env("AZURE_STORAGE_ACCOUNT")
AZURE_BLOB_CONTAINER = require_env("AZURE_BLOB_CONTAINER")

CONN_STR = require_env("AZURE_STORAGE_CONNECTION_STRING")

if not all([
    DATABRICKS_WORKSPACE_URL,
    DATABRICKS_TOKEN,
    DATABRICKS_JOB_ID,
    AZURE_STORAGE_ACCOUNT,
    # AZURE_BLOB_SAS_TOKEN,
]):
    raise RuntimeError("❌ Missing required environment variables")


# ------------------------------------------------------------
# Trigger Databricks job
# ------------------------------------------------------------
def trigger_job(payload: dict) -> int:
    print("🚀 Triggering Databricks job...")
    print("Payload:")
    print(json.dumps(payload, indent=2))

    url = f"{DATABRICKS_WORKSPACE_URL}/api/2.1/jobs/run-now"

    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "job_id": int(DATABRICKS_JOB_ID),
        "python_params": [json.dumps(payload)]
    }

    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()

    run_id = resp.json()["run_id"]
    print(f"✅ Job triggered. run_id = {run_id}")
    return run_id


# ------------------------------------------------------------
# Wait for Databricks job to finish
# ------------------------------------------------------------
def wait_for_run(run_id: int, poll_interval: int = 10) -> None:
    print("⏳ Waiting for Databricks job to complete...")

    url = f"{DATABRICKS_WORKSPACE_URL}/api/2.1/jobs/runs/get"
    headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

    while True:
        resp = requests.get(
            url,
            headers=headers,
            params={"run_id": run_id},
            timeout=30
        )
        resp.raise_for_status()

        run = resp.json()
        state = run["state"]["life_cycle_state"]
        result_state = run["state"].get("result_state")

        print(f"   Job state: {state}")

        if state == "TERMINATED":
            if result_state != "SUCCESS":
                raise RuntimeError(
                    f"❌ Databricks job failed: {json.dumps(run['state'], indent=2)}"
                )

            print("✅ Databricks job completed successfully")
            return

        time.sleep(poll_interval)


# ------------------------------------------------------------
# Read result.json from Azure Blob
# ------------------------------------------------------------
def fetch_drive_link_from_adls(payload: dict, timeout: int = 300) -> str:
    """
    Securely reads result.json from ADLS using account key.
    Works with private storage accounts.
    """

    connect_str = CONN_STR
    if not connect_str:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING not set")

    client_name = payload["client_name"]
    use_case_name = payload["use_case_name"]

    blob_path = f"{client_name}/{use_case_name}/result.json"

    print("🔎 Polling ADLS using Azure SDK")
    print(f"Blob path: finops-output/{blob_path}")

    blob_service = BlobServiceClient.from_connection_string(connect_str)
    blob_client = blob_service.get_blob_client(
        container="finops-output",
        blob=blob_path
    )

    start = time.time()
    attempt = 0

    while time.time() - start < timeout:
        attempt += 1
        try:
            print(f"   Attempt {attempt}: downloading result.json")
            data = blob_client.download_blob().readall()
            result = json.loads(data)

            if "drive_link" not in result:
                raise RuntimeError("drive_link missing in result.json")

            print("✅ result.json read successfully")
            return result["drive_link"]

        except Exception as e:
            print(f"   Not ready yet ({type(e).__name__})")
            time.sleep(5)

    raise TimeoutError("Timed out waiting for result.json in ADLS")


# ------------------------------------------------------------
# Orchestrator (call this from Streamlit / CLI)
# ------------------------------------------------------------
def run_job_and_get_gdrive_link(payload: dict) -> str:
    run_id = trigger_job(payload)
    wait_for_run(run_id)
    drive_link = fetch_drive_link_from_adls(payload)

    print("🎉 Google Drive link retrieved successfully")
    return drive_link
