import os
import shutil
import logging
from datetime import datetime
from tqdm import tqdm
from playwright.sync_api import sync_playwright

from config import Config, setup_logging
from workday_client import WorkdaySpendApiClient
from az_blob_utils import upload_to_blob
from utils import (
    initialize_csv,
    load_progress,
    save_progress,
    download_event,
    log_event_blob_links
)

def load_events_from_api() -> list[dict]:
    """
    Fetch event metadata from the Workday Spend API.

    Returns:
        list[dict]: A list of dictionaries with event ID and title.
    """
    headers = {
        "X-Api-Key": Config.API_KEY,
        "X-User-Token": Config.USER_TOKEN,
        "X-User-Email": Config.USER_EMAIL
    }

    logging.info(f"[API] Fetching events from endpoint: {Config.API_EVENTS_ENDPOINT}")
    client = WorkdaySpendApiClient(base_url=Config.API_BASE_URL, headers=headers)
    events = client.fetch(endpoint=Config.API_EVENTS_ENDPOINT, paginated=True)

    if not events:
        logging.warning("[API] No events received from API.")
        return []

    logging.info(f"[API] Retrieved {len(events)} events.")
    return [{"id": event["id"], "title": event["attributes"]["title"]} for event in events]

def main():
    """
    Main execution flow for downloading, uploading, and logging Workday event files.
    """
    setup_logging()
    initialize_csv()

    start_time = datetime.now()
    logging.info(f"[Startup] Workday event extraction started at {start_time}")

    events = load_events_from_api()
    if not events:
        logging.error("[Startup] Event list is empty. Exiting.")
        return

    start_index = load_progress()
    events_to_process = events[start_index:]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Manual login step
        page.goto(Config.WD_LOGIN_URL)
        page.wait_for_load_state("domcontentloaded")
        while not page.url.startswith(Config.WD_HOME_URL):
            logging.info(f"[Login] Waiting for login. Current URL: {page.url}")
            page.wait_for_timeout(Config.LOGIN_TIMEOUT)

        logging.info(f"[Login] Login successful. URL: {page.url}")

        # Main processing loop
        for idx, event in enumerate(tqdm(events_to_process, desc="Processing events", total=len(events_to_process))):
            event_id = event["id"]
            event_title = event["title"]

            logging.info(f"[Event] Processing event {event_id}: {event_title}")
            os.makedirs(Config.TEMP_DIR, exist_ok=True)

            # Step 1: Download files
            local_files = download_event(event_id, page)

            # Step 2: Upload to blob
            blob_urls = [upload_to_blob(path, event_id) for path in local_files]

            # Step 3: Log results
            log_event_blob_links(event_id, event_title, blob_urls)

            # Step 4: Clean temp folder
            shutil.rmtree(Config.TEMP_DIR, ignore_errors=True)

            # Step 5: Save progress
            save_progress(start_index + idx + 1)

        browser.close()

    end_time = datetime.now()
    duration = end_time - start_time

    logging.info(f"[Complete] Extraction finished at {end_time}")
    logging.info(f"[Complete] Duration: {duration}")
    logging.info(f"[Complete] Total events processed: {len(events_to_process)}")

if __name__ == "__main__":
    main()
