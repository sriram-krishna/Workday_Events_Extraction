from playwright.sync_api import sync_playwright
import os

DOWNLOAD_DIR = ""

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto("https://file-examples.com/index.php/sample-documents-download/sample-xls-download/")
        page.wait_for_load_state("domcontentloaded")

        # Find and click the first download button
        with page.expect_download() as download_info:
            page.click('a[href*="file_example_XLS_10.xls"]')  # Adjust if needed

        download = download_info.value
        download.save_as(os.path.join(DOWNLOAD_DIR, "sample_download.xls"))
        print("Downloaded file successfully.")

        browser.close()

if __name__ == "__main__":
    run()
