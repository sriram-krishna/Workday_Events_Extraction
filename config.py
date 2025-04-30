import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Central configuration class that loads environment variables
    for API access and Azure Blob Storage settings.
    """

    # API settings
    API_BASE_URL: str = os.getenv("API_BASE_URL")
    API_EVENTS_ENDPOINT: str = os.getenv("API_EVENTS_ENDPOINT")
    API_ATTACHMENTS_ENDPOINT: str = os.getenv("API_ATTACHMENTS_ENDPOINT")
    API_KEY: str = os.getenv("API_KEY")
    USER_TOKEN: str = os.getenv("USER_TOKEN")
    USER_EMAIL: str = os.getenv("USER_EMAIL")

    # Azure Blob Storage settings
    AZURE_STORAGE_CONNECTION_STRING: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME: str = os.getenv("AZURE_CONTAINER_NAME")
    AZURE_BLOB_PREFIX: str = os.getenv("AZURE_BLOB_PREFIX")