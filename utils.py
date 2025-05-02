import logging
import os
import json

PROGRESS_FILE = "progress.json"

def setup_logging():
    """Configure application-wide logging."""
    logging.basicConfig(
        filename="workday_import.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.getLogger("azure.storage.blob").setLevel(logging.WARNING)

def save_progress(index: int):
    """Save current processing index for resume support."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_index": index}, f)


def load_progress() -> int:
    """Load last processing index from progress file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_index", 0)
    return 0
