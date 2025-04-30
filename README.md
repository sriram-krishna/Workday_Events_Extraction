# 📦 Workday Spend Events Importer

> Import Workday Spend events and attachments to Azure Blob — organized, traceable, and audit-friendly.

---

## 📚 Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [How to Run](#how-to-run)
- [Azure Blob Structure](#azure-blob-structure)
- [Logging and Audit](#logging-and-audit)
- [Built With](#built-with)
- [Author / Maintainer](#author--maintainer)

---

## ✅ Features

- 🔁 Supports paginated event retrieval from Workday API
- 📄 Saves event metadata as both a full and per-event JSON
- 📎 Downloads all attachments tied to each event
- ☁️ Uploads files and metadata to Azure Blob Storage
- 📝 Timestamped logging and failure tracking
- 📊 Final summary with event and attachment counts

---

## 🚀 Getting Started

### ⚙️ Prerequisites

- Python 3.12+
- Access to Workday Spend API credentials (API key, token, email)
- Azure Storage account and container set up

### 1. Clone this repository

```bash
git clone https://github.com/sriram-krishna/workdayspend-events-importer.git
cd workdayspend-events-importer
```

### 2. Install required packages

```bash
pip install -r requirements.txt
```

### 3. Create your `.env` file

```ini
# Workday API
API_BASE_URL=https://api.workdayspend.com/services
API_EVENTS_ENDPOINT=/events/v1/events
API_ATTACHMENTS_ENDPOINT=/attachments/v1/attachments
API_KEY=your_api_key_here
USER_TOKEN=your_user_token
USER_EMAIL=you@example.com

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_CONTAINER_NAME=your_container_name
AZURE_BLOB_PREFIX=your_blob_prefix  # Optional: defines folder structure prefix in Blob Storage
```

---

## ▶️ How to Run

```bash
python main.py
```

All logs will be written to:
- `workday_import.log`
- Failed attachments: `failed_attachments.csv`

---

## 📁 Azure Blob Structure

```
${AZURE_CONTAINER_NAME}/
├── all_events.json
├── <event_id>/
│   ├── <event_id>_event.json
│   └── attachments/
│       ├── attachments.json
│       └── file1.pdf
│       └── file2.docx
```

---

## 📊 Logging and Audit

All actions and failures are logged with timestamps.

Example `workday_import.log` output:

```
2025-04-30 10:00:00 [INFO] Uploaded event JSON for event 12345 to: ${AZURE_CONTAINER_NAME}/12345/12345_event.json
2025-04-30 10:00:03 [INFO] Uploaded attachment invoice.pdf for event 12345 to: wdevents/12345/attachments/invoice.pdf
```

Failed attachment entries will appear in `failed_attachments.csv` with event ID, attachment ID, and reason.

---

## 🧩 Built With

- [Python 3.12](https://www.python.org/)
- [requests](https://docs.python-requests.org/en/latest/)
- [azure-storage-blob](https://pypi.org/project/azure-storage-blob/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## 👨‍💻 Author / Maintainer

Created and maintained by **Sriram Krishna**  

---
