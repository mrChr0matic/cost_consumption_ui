from databricks_trigger import run_job_and_get_gdrive_link

# -------------------------------
# Sample payload (same as Streamlit)
# -------------------------------
payload = {
    "image_uri": "https://res.cloudinary.com/dug1uuu9g/image/upload/v1765951816/mj2ulwuyyidudae5kenj.jpg",  # use a real image URL
    "client_name": "sample",
    "use_case_name": "sample",
    "markets": [
        {"market": "M1", "multiplier": 1.0, "start_month": 1}
    ],
    "user_prompt": "Assume enterprise-grade HA architecture",
    "budget": 250000
}

# -------------------------------
# Run test
# -------------------------------
if __name__ == "__main__":
    print("Triggering Databricks job...")

    try:
        drive_link = run_job_and_get_gdrive_link(payload)
    except Exception as e:
        print("❌ Job failed")
        raise

    print("\n✅ Job completed successfully")
    print("Google Drive link:")
    print(drive_link)
