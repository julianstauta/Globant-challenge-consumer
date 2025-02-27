import functions_framework
import pandas as pd
import requests
from google.cloud import storage

# Cloud Run API endpoint
API_URL = "https://globant-challenge-170792856253.us-central1.run.app/upload-data"  # Update with actual URL

# Max batch size
BATCH_SIZE = 1000

# Columnames
dict_col_names = {
    "hired_employees": ["id", "name", "datetime", "department_id", "job_id"],
    "departments" : ["id", "department"],
    "jobs": ["id", "job"]
}

# Google Cloud Storage Client
storage_client = storage.Client()

def process_csv(file_path, table):
    """Reads, processes the CSV, and sends valid rows to API."""
    try:
        # Read CSV file
        df = pd.read_csv(file_path, names=dict_col_names.get(table), header=None)

        # Separate missing data
        missing_data_df = df[df.isnull().any(axis=1)]
        valid_data_df = df.dropna()

        print(f"Rows with missing values: {len(missing_data_df)}")
        print(f"Valid rows to insert: {len(valid_data_df)}")

        # Process only valid rows
        batches = [valid_data_df.iloc[i:i + BATCH_SIZE] for i in range(0, len(valid_data_df), BATCH_SIZE)]

        # Send each batch
        for i, batch in enumerate(batches):
            send_batch_to_api(batch, i + 1, table)

    except Exception as e:
        print(f"Error processing CSV: {e}")

def send_batch_to_api(batch_df, batch_number, table):
    """Sends a batch of data to the API."""
    try:
        batch_data = batch_df.to_dict(orient="records")
        payload = {table: batch_data}

        response = requests.post(API_URL, json=payload)

        if response.status_code == 200:
            print(f"Batch {batch_number}: {len(batch_df)} rows inserted in table {table}")
        else:
            print(f"Batch {batch_number} Error: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Failed to send batch {batch_number}: {e}")

@functions_framework.cloud_event
def gcs_trigger(cloud_event):
    """Cloud Function Triggered when a new file is uploaded to GCS."""
    data = cloud_event.data

    # Extract bucket name and file name
    bucket_name = data["bucket"]
    file_name = data["name"]

    print(f"New file detected: gs://{bucket_name}/{file_name}")

    # Download the file from GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    local_file_path = f"/tmp/{file_name}"
    blob.download_to_filename(local_file_path)

    print(f"Downloaded {file_name} to {local_file_path}")

    # Process the CSV file
    if "employee" in f"{file_name}".lower():
        process_csv(local_file_path, "hired_employees")
    elif "department" in f"{file_name}".lower():
        process_csv(local_file_path, "departments")
    elif "job" in f"{file_name}".lower():
        process_csv(local_file_path, "jobs")
    else:
        print(f"File inserted des not belongs to any of the tables")

