# config.py
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

def parse_int(env_var, default):
    try:
        return int(os.getenv(env_var, default))
    except (TypeError, ValueError):
        return default

class Config:
    """
    Global configuration for Workday data extraction pipeline.
    Values are loaded from environment variables (use .env in development).
    """

    # === Workday API ===
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_EVENTS_ENDPOINT = os.getenv("API_EVENTS_ENDPOINT")
    API_KEY = os.getenv("API_KEY")
    USER_TOKEN = os.getenv("USER_TOKEN")
    USER_EMAIL = os.getenv("USER_EMAIL")

    # === Workday UI Navigation ===
    WD_LOGIN_URL = os.getenv("WD_LOGIN_URL")
    WD_HOME_URL = os.getenv("WD_HOME_URL")
    WD_ATTACHMENTS_URL = os.getenv("WD_ATTACHMENTS_URL", "/attachments")
    WD_DASHBOARD_URL = os.getenv("WD_DASHBOARD_URL", "/dashboard")
    WD_BID_EXPORT_URL = os.getenv("WD_BID_EXPORT_URL", "/bid-export")

    # === Azure Blob Storage ===
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
    AZURE_BLOB_PREFIX = os.getenv("AZURE_BLOB_PREFIX", "")

    # === Local File Paths ===
    TEMP_DIR = os.getenv("TEMP_DIR", "./temp_downloads")
    CSV_FILE = os.getenv("CSV_FILE", "downloaded_files.csv")
    PROGRESS_FILE = os.getenv("PROGRESS_FILE", "progress.json")

    # === Workday API Settings ===
    WD_API_TIMEOUT = parse_int("WD_API_TIMEOUT", 30)  # in seconds
    WD_API_RETRY_SLEEP = parse_int("WD_API_RETRY_SLEEP", 1)  # in seconds
    WD_API_MAX_RETRIES = parse_int("WD_API_MAX_RETRIES", 3)
    WD_API_PAGE_SIZE = parse_int("WD_API_PAGE_SIZE", 100)

    # === CSV Fieldnames ===
    CSV_FIELDNAMES = [
        "event_id",
        "title",
        "file1",
        "file2",
        "file3"
    ]

    # === Timeouts and Waits ===
    DOWNLOAD_TIMEOUT = parse_int("DOWNLOAD_TIMEOUT", 30000)  # in ms
    LOGIN_TIMEOUT = parse_int("LOGIN_TIMEOUT", 180000)       # in ms

    @classmethod
    def validate(cls):
        """
        Validate critical configuration values at startup.
        Raises:
            RuntimeError: If any required config value is missing.
        """
        required = {
            "API_BASE_URL": cls.API_BASE_URL,
            "API_EVENTS_ENDPOINT": cls.API_EVENTS_ENDPOINT,
            "API_KEY": cls.API_KEY,
            "USER_TOKEN": cls.USER_TOKEN,
            "USER_EMAIL": cls.USER_EMAIL,
            "WD_LOGIN_URL": cls.WD_LOGIN_URL,
            "WD_HOME_URL": cls.WD_HOME_URL,
            "AZURE_STORAGE_CONNECTION_STRING": cls.AZURE_STORAGE_CONNECTION_STRING,
            "AZURE_CONTAINER_NAME": cls.AZURE_CONTAINER_NAME,
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise RuntimeError(f"Missing required configuration values: {', '.join(missing)}")

def setup_logging():
    """
    Configure global logging to log both to file and console.
    """
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler("workday_import.log")
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    logging.getLogger("azure.storage.blob").setLevel(logging.WARNING)
