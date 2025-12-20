# Uber Receipt Expense Automation

Automatically extract expense data from Uber receipt PDFs and generate consolidated expense reports.

## Features

- **Extract data from Uber PDFs**: Employee name, date, and total amount
- **Two modes of operation**:
  - **Web UI** (Streamlit): Upload PDFs or link a Google Drive folder → download CSV
  - **Cron script**: Automated sync from Google Drive → Google Sheets
- **Google Drive integration**: Pull receipts directly from a shared folder

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Google Drive folder access

Your Google Drive folder containing Uber receipts must be shared as:
> **Anyone with the link → Viewer**

Otherwise, the download will fail.

### 3. Google Sheets API (for cron mode only)

1. Create a service account in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Sheets API
3. Download the JSON credentials file and save it as `uber-sheet-cron-5009f7af7bd6.json` (or update `SERVICE_ACCOUNT_FILE` in `cron.py`)
4. Share your target Google Sheet with the service account email

## Usage

### Web UI (Streamlit)

```bash
streamlit run run.py
```

Then open `http://localhost:8501` in your browser. You can:
- Upload Uber receipt PDFs directly
- Paste a Google Drive folder link

The app will display extracted data and let you download a CSV.

### Automated Cron Script

```bash
python cron.py
```

This will:
1. Download PDFs from the configured Google Drive folder
2. Extract expense data from each receipt
3. Update the configured Google Sheet

#### CLI options

```bash
python cron.py --folder /path/to/local/pdfs   # Use local folder instead of downloading
python cron.py --no-download                   # Skip download (for testing)
```

### Configuration

Edit the constants at the top of `cron.py`:

```python
GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/..."
GOOGLE_SHEET_ID = "your-sheet-id"
GOOGLE_SHEET_TAB_NAME = "Sheet1"
SERVICE_ACCOUNT_FILE = "uber-sheet-cron-5009f7af7bd6.json"
EMPLOYEE_NAME_OVERRIDE = None  # Set to override name from PDFs
```

## Output Format

| Column | Description |
|--------|-------------|
| Employee Name | From PDF or override |
| Expense Vendor Name | "Uber" |
| Expense Description | Transportation description |
| Date | Extracted trip date (YYYY-MM-DD) |
| Reference of Receipt | PDF filename |
| Total | Amount in INR |

## Project Structure

```
├── run.py           # Streamlit web app
├── cron.py          # Automated Google Sheets sync script
├── utils.py         # Shared utility functions
├── requirements.txt # Python dependencies
└── *.json           # Service account credentials (not committed)
```

