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

    # Step 2: Upload complete events list
    all_events_blob_path = f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/all_events.json"
    upload_json_to_blob(data=events, blob_path=all_events_blob_path)

    # Step 3: Process each event
    for event in events:
        event_id = event.get("id")
        if not event_id:
            logging.warning("Skipping event with missing ID.")
            continue

        event_count += 1

        # Upload individual event JSON
        event_blob_path = f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/{event_id}/{event_id}_event.json"
        upload_json_to_blob(data=event, blob_path=event_blob_path)
        logging.info(f"Uploaded event JSON for event {event_id} to: {event_blob_path}")

        # Upload list of attachments for this event
        attachments = event.get().get ("attachments", [])
        attachments_blob_path = f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/{event_id}/attachments/attachments.json"
        upload_json_to_blob(data=attachments, blob_path=attachments_blob_path)
        logging.info(f"Uploaded attachments metadata for event {event_id} to: {attachments_blob_path}")

        # Step 4: Process each attachment
        for attachment in attachments:
            attachment_id = attachment.get("id")
            if not attachment_id:
                logging.warning(f"Skipping attachment with missing ID under event {event_id}.")
                continue

            # Fetch attachment metadata
            metadata = client.fetch(
                endpoint=f"{Config.API_ATTACHMENTS_ENDPOINT}/{attachment_id}",
                paginated=False
            )
            if not metadata:
                logging.error(f"Failed to fetch metadata for attachment {attachment_id} under event {event_id}.")
                log_failed_attachment(event_id, attachment_id, "No metadata")
                failed_attachments += 1
                continue

            download_url = metadata.get("attributes", {}).get("download_url")
            if not download_url:
                logging.warning(f"No download URL for attachment {attachment_id} under event {event_id}.")
                log_failed_attachment(event_id, attachment_id, "Missing download URL")
                failed_attachments += 1
                continue

            filename = extract_filename_from_url(download_url) or f"{attachment_id}.bin"
            attachment_blob_path = f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/{event_id}/attachments/{filename}"

            try:
                upload_stream_to_blob(
                    download_url=download_url,
                    blob_path=attachment_blob_path,
                    event_id=event_id,
                    attachment_id=attachment_id
                )
                logging.info(f"Uploaded attachment {filename} for event {event_id} to: {attachment_blob_path}")
                attachment_count += 1
            except Exception as e:
                logging.error(f"Failed to upload attachment {attachment_id} for event {event_id}: {str(e)}")
                log_failed_attachment(event_id, attachment_id, str(e))
                failed_attachments += 1

    end_time = datetime.now()
    duration = end_time - start_time

    logging.info("=== Workday Import Completed ===")
    logging.info(f"Total events processed: {event_count}")
    logging.info(f"Total attachments uploaded: {attachment_count}")
    logging.info(f"Total failed attachments: {failed_attachments}")
    logging.info(f"Duration: {duration}")


if __name__ == "__main__":
    main()