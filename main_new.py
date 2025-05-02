from config import Config
from workday_client import WorkdaySpendApiClient
from playwright.sync_api import sync_playwright
from az_blob_utils import upload_to_blob
from utils import setup_logging, save_progress, load_progress, download_event
from datetime import datetime
from tqdm import tqdm
import logging

def load_events_from_api():
    headers = {
        "X-Api-Key": Config.API_KEY,
        "X-User-Token": Config.USER_TOKEN,
        "X-User-Email": Config.USER_EMAIL
    }
    logging.info(f"Fetching events from API: {Config.API_EVENTS_ENDPOINT}")
    client = WorkdaySpendApiClient(base_url=Config.API_BASE_URL, headers=headers)
    events = client.fetch(endpoint=Config.API_EVENTS_ENDPOINT, paginated=True)
    if not events:
        logging.warning("No events retrieved from Workday Spend API.")
        return
    logging.info(f"Fetched {len(events)} events from API.")

    events_list = [
        {
            "id": events["id"],
            "title": events["attributes"]["title"]
        }
        for events in events
    ]
    return events_list

def main():
    setup_logging()
    start_time = datetime.now()
    logging.info(f"Starting Workday Events Extraction at {start_time}")

    events = load_events_from_api()
    if not events:
        return
    logging.info(f"Fetched {len(events)} events from Workday Spend API.")

    start_index = load_progress()
    events_to_process = events[start_index:]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(Config.WD_LOGIN_URL)
        page.wait_for_load_state("domcontentloaded")
        while not page.url.startswith(Config.WD_HOME_URL):
            print("Waiting for login... current URL:", page.url)
            page.wait_for_timeout(30000)
        logging.info("Logged in successfully. current URL:", page.url)
        for idx, event in enumerate(tqdm(events_to_process, desc="Processing events", total=len(events_to_process))):
            event_id = event["id"]
            print(event_id)
            download_event(event_id, page)
            upload_to_blob(f"{Config.AZURE_BLOB_PREFIX.rstrip('/')}/events/{event_id}")
            save_progress(idx+1)    
    browser.close()
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"Ending Workday Events Extraction at {end_time}")
    logging.info(f"Workday Events Extraction completed in {duration}")
    logging.info(f"Saved progress at index {start_index}")
    logging.info(f"Total events processed: {start_index + len(events_to_process)}")

if __name__ == "__main__":
    main()