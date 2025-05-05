import logging
import time
import requests
from typing import Union, Optional
from config import Config

class WorkdaySpendApiClient:
    """
    A client to interact with the Workday Spend API.
    Supports paginated and non-paginated GET requests with automatic retry handling.
    """

    def __init__(self, base_url: str, headers: dict):
        """
        Initialize the client with a base API URL and required headers.
        
        Args:
            base_url (str): Root API URL, e.g. "https://api.workday.com/v1"
            headers (dict): Required auth headers (API key, token, email, etc.)
        """
        if not base_url:
            raise ValueError("Base URL is required.")
        if not headers or not isinstance(headers, dict):
            raise ValueError("Headers must be a valid dictionary.")

        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.session = requests.Session()

        # Constants for retry logic
        self.page_size = Config.WD_API_PAGE_SIZE
        self.timeout_seconds = Config.WD_API_TIMEOUT
        self.retry_sleep_seconds = Config.WD_API_RETRY_SLEEP
        self.max_retries = Config.WD_API_MAX_RETRIES


    def fetch(self, endpoint: str, paginated: bool) -> Union[list, dict, None]:
        """
        Fetch data from the API. Supports pagination if required.

        Args:
            endpoint (str): API endpoint (e.g. "/events")
            paginated (bool): True to follow paginated responses; False for single response

        Returns:
            Union[list, dict, None]: Parsed data or None on failure
        """
        if not endpoint:
            raise ValueError("API endpoint is required.")

        url = f"{self.base_url}{endpoint}?page[size]={self.page_size}"
        all_data = []

        try:
            while url:
                logging.info(f"[Workday API] Fetching: {url}")
                response = self._get_with_retries(url)

                if not response:
                    logging.error(f"[Workday API] No response received for: {url}")
                    break

                try:
                    payload = response.json()
                except Exception as parse_error:
                    logging.error(f"[Workday API] Failed to parse JSON from {url}: {parse_error}")
                    break

                if paginated:
                    records = payload.get("data", [])
                    all_data.extend(records)
                    url = payload.get("links", {}).get("next")
                    time.sleep(0.25)  # brief pause to avoid rate-limiting
                else:
                    return payload.get("data", [])

            return all_data if paginated else None

        except Exception as e:
            logging.exception(f"[Workday API] Unexpected error during fetch from {endpoint}: {e}")
            return None

    def _get_with_retries(self, url: str) -> Optional[requests.Response]:
        """
        Perform a GET request with retry support on 429 or transient errors.

        Args:
            url (str): The full request URL

        Returns:
            Response object if successful, else None
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, headers=self.headers, timeout=self.timeout_seconds)

                if response.status_code == 429:
                    logging.warning(f"[Workday API] Rate limited (429). Retrying in {self.retry_sleep_seconds}s...")
                    time.sleep(self.retry_sleep_seconds)
                    continue

                response.raise_for_status()
                return response

            except requests.HTTPError as http_err:
                logging.warning(f"[Workday API] HTTP error (attempt {attempt}): {http_err}")
                if attempt == self.max_retries:
                    logging.error(f"[Workday API] Max retries reached for {url}")
                else:
                    time.sleep(self.retry_sleep_seconds)

            except requests.RequestException as req_err:
                logging.error(f"[Workday API] Request failed (attempt {attempt}): {req_err}")
                if attempt == self.max_retries:
                    logging.error(f"[Workday API] Giving up after {self.max_retries} attempts.")
                else:
                    time.sleep(self.retry_sleep_seconds)

        return None
