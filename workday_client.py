import logging
import time
import requests


class WorkdaySpendApiClient:
    """
    A client to interact with the Workday Spend API.
    Handles paginated and non-paginated requests with basic retry support.
    """

    def __init__(self, base_url: str, headers: dict):
        if not base_url:
            raise ValueError("Base URL is required.")
        if not headers or not isinstance(headers, dict):
            raise ValueError("Headers must be a valid dictionary.")

        self.base_url = base_url.rstrip("/")
        self.headers = headers
        self.session = requests.Session()

    def fetch(self, endpoint: str, paginated: bool) -> list | dict | None:
        """
        Fetch data from the specified API endpoint.

        Args:
            endpoint (str): API endpoint (e.g., /events)
            paginated (bool): Whether to paginate through results

        Returns:
            list | dict | None: Aggregated data (list) if paginated, else a single dict response.
        """
        if not endpoint:
            raise ValueError("Endpoint is required.")

        url = f"{self.base_url}{endpoint}"
        all_data = []

        try:
            while url:
                logging.info(f"Fetching data from: {url}")
                response = self.session.get(url, headers=self.headers, timeout=30)

                if response.status_code == 429:
                    logging.warning("Rate limited. Retrying after 1 second...")
                    time.sleep(1)
                    continue

                response.raise_for_status()
                payload = response.json()

                if paginated:
                    records = payload.get("data", [])
                    all_data.extend(records)
                    url = payload.get("links", {}).get("next")
                    time.sleep(0.25)  # throttle to respect rate limits
                else:
                    return payload

            return all_data if paginated else None

        except requests.RequestException as error:
            logging.error(f"Request failed for endpoint {endpoint}: {error}")
            return None
