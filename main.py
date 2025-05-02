import logging
from workday_client import WorkdaySpendApiClient
from az_blob_utils import (
    extract_filename_from_url,
    upload_stream_to_blob,
    upload_json_to_blob,
    log_failed_attachment
)
from config import Config
from datetime import datetime


def main():
    # Configure logging
    logging.basicConfig(
        filename="workday_import.log",
        level=logging.INFO,
        format="%Y-%m-%d %H:%M:%S [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.getLogger("azure.storage.blob").setLevel(logging.WARNING)

    start_time = datetime.now()
    logging.info("=== Workday Import Started ===")

    event_count = 0
    attachment_count = 0
    failed_attachments = 0

    # Initialize Workday Spend API client
    headers = {
        "X-Api-Key": Config.API_KEY,
        "X-User-Token": Config.USER_TOKEN,
        "X-User-Email": Config.USER_EMAIL
    }
    client = WorkdaySpendApiClient(base_url=Config.API_BASE_URL, headers=headers)

    # Step 1: Fetch all events
    events = client.fetch(endpoint=Config.API_EVENTS_ENDPOINT, paginated=True)
    if not events:
        logging.warning("No events retrieved from Workday Spend API.")
        return

    logging.info(f"Fetched {len(events)} events from API.")

    # Step 2: Filter events to get event id and event name
    events_list = [
        {
            "id": event["id"],
            "name": event["attributes"]["title"]
        }
        for event in events
    ]
    
    # Step 3: Loop over each event and Generate URLs
    for event in events_list[:10]:
        event_id  = event["id"]
        title = event["name"]
        logging.info(f"Processing Event: {event_id}")
        download_event_files(page, event_id)
    # Step 4: Copy attachments to Blob Storage
    event_blob_path = f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/events/{event_id}"
    upload_files_to_blob(event_blob_path)

    # Step 5: Upload complete events list



    end_time = datetime.now()
    duration = end_time - start_time

    logging.info("=== Workday Import Completed ===")
    logging.info(f"Total events processed: {event_count}")
    logging.info(f"Total attachments uploaded: {attachment_count}")
    logging.info(f"Total failed attachments: {failed_attachments}")
    logging.info(f"Duration: {duration}")


if __name__ == "__main__":
    main()