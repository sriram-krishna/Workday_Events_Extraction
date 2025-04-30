import logging
import csv
import json
import requests
import os
from urllib.parse import urlparse, unquote
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from config import Config

# Configure application-wide logging
logging.basicConfig(
    filename="workday_import.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def log_failed_attachment(event_id: str, attachment_id: str, reason: str):
    """
    Log failed attachment metadata to a CSV for audit and reprocessing.
    """
    with open("failed_attachments.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([event_id, attachment_id, reason])


def upload_json_to_blob(data: dict, blob_path: str):
    """
    Upload a Python dictionary as a JSON file to Azure Blob Storage.
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(Config.AZURE_CONTAINER_NAME)

        if not container_client.exists():
            container_client.create_container()

        blob_client = container_client.get_blob_client(blob_path)
        json_data = json.dumps(data, indent=4)
        blob_client.upload_blob(json_data, overwrite=True)

        logging.info(f"Uploaded JSON to blob: {blob_path}")
    except Exception as e:
        logging.error(f"Failed to upload JSON to blob {blob_path}: {e}")


def upload_stream_to_blob(download_url: str, blob_path: str, event_id: str = "", attachment_id: str = ""):
    """
    Stream a file from a download URL directly into Azure Blob Storage.
    Optionally includes event and attachment IDs for clearer logging.
    """
    try:
        with requests.get(download_url, stream=True, timeout=30) as response:
            response.raise_for_status()

            blob_service_client = BlobServiceClient.from_connection_string(Config.AZURE_STORAGE_CONNECTION_STRING)
            container_client = blob_service_client.get_container_client(Config.AZURE_CONTAINER_NAME)

            if not container_client.exists():
                container_client.create_container()

            blob_client = container_client.get_blob_client(blob_path)
            blob_client.upload_blob(response.raw, overwrite=True)

            logging.info(f"Uploaded attachment to blob: {blob_path}")
    except Exception as e:
        logging.error(f"Failed to stream upload from {download_url} to {blob_path}: {e}")
        if event_id and attachment_id:
            log_failed_attachment(event_id, attachment_id, str(e))


def extract_filename_from_url(download_url: str) -> str:
    """
    Extract the file name from a download URL, decoding URL-encoded characters.
    """
    try:
        path = urlparse(download_url).path
        filename = os.path.basename(path)
        return unquote(filename) if filename else None
    except Exception as e:
        logging.error(f"Failed to extract filename from URL: {e}")
        return None
