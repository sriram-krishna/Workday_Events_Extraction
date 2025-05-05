import os
import logging
from azure.storage.blob import BlobServiceClient
from config import Config

def upload_to_blob(local_path: str, event_id: str) -> str:
    """
    Upload a file from the local filesystem to Azure Blob Storage.

    The blob will be stored under a structured path:
        {AZURE_BLOB_PREFIX}/<event_id>/<filename>

    Args:
        local_path (str): Full path to the local file to be uploaded.
        event_id (str): The Workday event ID used to organize blobs by event.

    Returns:
        str: Azure Blob Storage URL to the uploaded file, or empty string on failure.
    """
    try:
        filename = os.path.basename(local_path)
        blob_path = f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/{event_id}/{filename}"

        # Initialize Azure Blob client
        blob_service_client = BlobServiceClient.from_connection_string(
            Config.AZURE_STORAGE_CONNECTION_STRING
        )
        container_client = blob_service_client.get_container_client(Config.AZURE_CONTAINER_NAME)

        # Create container if it doesn't exist
        if not container_client.exists():
            logging.info(f"[Azure] Container '{Config.AZURE_CONTAINER_NAME}' not found. Creating...")
            container_client.create_container()

        # Upload the file
        blob_client = container_client.get_blob_client(blob_path)
        with open(local_path, "rb") as file_data:
            blob_client.upload_blob(file_data, overwrite=True)

        logging.info(f"[Azure] Uploaded file: {blob_path}")

        # Return full blob URL
        return f"{Config.AZURE_BLOB_BASE_URL}/{Config.AZURE_CONTAINER_NAME}/{blob_path}"

    except Exception as e:
        logging.error(f"[Azure] Failed to upload '{local_path}' for event '{event_id}': {e}")
        return ""
