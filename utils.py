import logging
import os
import json
import csv
import shutil
from config import Config
from playwright.sync_api import Page

def save_progress(index: int):
    """
    Save the current processing index to a file for resume support.
    """
    with open(Config.PROGRESS_FILE, "w") as f:
        json.dump({"last_index": index}, f)

def load_progress() -> int:
    """
    Load the last saved processing index.
    Returns 0 if no file exists.
    """
    if os.path.exists(Config.PROGRESS_FILE):
        with open(Config.PROGRESS_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_index", 0)
    return 0

def initialize_csv():
    """
    Create the CSV file and write headers if it doesn't already exist.
    """
    if not os.path.exists(Config.CSV_FILE):
        with open(Config.CSV_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=Config.CSV_FIELDNAMES)
            writer.writeheader()

def log_event_blob_links(event_id: str, title: str, blob_urls: list[str]):
    """
    Log the blob URLs of uploaded files to the CSV file.

    Args:
        event_id (str): ID of the event.
        title (str): Event title.
        blob_urls (list): List of URLs to files stored in blob.
    """
    row = {
        "event_id": event_id,
        "title": title,
        "file1": blob_urls[0] if len(blob_urls) > 0 else "",
        "file2": blob_urls[1] if len(blob_urls) > 1 else "",
        "file3": blob_urls[2] if len(blob_urls) > 2 else ""
    }
    with open(Config.CSV_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=Config.CSV_FIELDNAMES)
        writer.writerow(row)

def cleanup_temp_dir():
    """
    Remove and recreate the temp directory to avoid disk buildup.
    """
    shutil.rmtree(Config.TEMP_DIR, ignore_errors=True)
    os.makedirs(Config.TEMP_DIR, exist_ok=True)

def download_event(event_id: str, page: Page) -> list[str]:
    """
    Automate the browser to download all necessary files for a given event.

    Args:
        event_id (str): The Workday event ID.
        page (Page): The Playwright page instance.

    Returns:
        list[str]: List of local file paths for downloaded files.
    """
    downloaded_files = []
    os.makedirs(Config.TEMP_DIR, exist_ok=True)

    try:
        # 1. Download from Attachments page
        page.goto(f"{Config.WD_HOME_URL}/{event_id}{Config.WD_ATTACHMENTS_URL}")
        page.wait_for_load_state("networkidle")
        page.click("[data-role='download-button']")
        page.wait_for_selector("[data-role='confirm']", timeout=Config.DOWNLOAD_TIMEOUT)
        confirm_btn = page.locator("[data-role='confirm']")
        confirm_etl = confirm_btn.element_handle()
        page.wait_for_function(
            "el => el && el.getAttribute('href') && el.getAttribute('href') !== ''",
            arg=confirm_etl,
            timeout=Config.DOWNLOAD_TIMEOUT
        )
        with page.expect_download() as d1:
            page.click("[data-role='confirm']")
        download1 = d1.value
        file1 = os.path.join(Config.TEMP_DIR, download1.suggested_filename)
        download1.save_as(file1)
        downloaded_files.append(file1)
        logging.info(f"Downloaded attachments for {event_id}: {file1}")

        # 2. Dashboard file
        page.goto(f"{Config.WD_HOME_URL}/{event_id}{Config.WD_DASHBOARD_URL}")
        page.wait_for_load_state("networkidle")
        page.click("[data-role='download-button']")
        page.wait_for_selector("[data-role='confirm']", timeout=Config.DOWNLOAD_TIMEOUT)
        confirm_btn = page.locator("[data-role='confirm']")
        confirm_etl = confirm_btn.element_handle()
        page.wait_for_function(
            "el => el && el.getAttribute('href') && el.getAttribute('href') !== ''",
            arg=confirm_etl,
            timeout=Config.DOWNLOAD_TIMEOUT
        )
        with page.expect_download() as d2:
            page.click("[data-role='confirm']")
        download2 = d2.value
        file2 = os.path.join(Config.TEMP_DIR, download2.suggested_filename)
        download2.save_as(file2)
        downloaded_files.append(file2)
        logging.info(f"Downloaded dashboard for {event_id}: {file2}")

        # 3. Bid Export file
        page.goto(f"{Config.WD_HOME_URL}/{event_id}{Config.WD_BID_EXPORT_URL}")
        page.wait_for_load_state("networkidle")
        page.click("[data-role='export-sourcing-event']")
        page.wait_for_selector("[data-role='download-exported-file']", timeout=Config.DOWNLOAD_TIMEOUT)
        with page.expect_download() as d3:
            page.click("[data-role='download-exported-file']")
        download3 = d3.value
        file3 = os.path.join(Config.TEMP_DIR, download3.suggested_filename)
        download3.save_as(file3)
        downloaded_files.append(file3)
        logging.info(f"Downloaded bid export for {event_id}: {file3}")

    except Exception as e:
        logging.error(f"Download failed for event {event_id}: {e}")

    return downloaded_files
