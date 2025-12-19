#!/usr/bin/env python3
import os
import re
import tempfile
from datetime import datetime

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from utils import (
    extract,
    extract_date,
    download_drive_folder,
    extract_text_from_pdf,
    list_pdf_files,
)

# ================== CONFIG ==================

# Google Drive folder with all your Uber receipt PDFs
GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1lkNOkV3HpUE-o7iWfpsz-PNEIbz3Fb3Z"

# Google Sheet config
GOOGLE_SHEET_ID = "1ZoyuN_aFIa3S6_qNq_qpIqnb3k-GtTPSdPx3zPzALU0"   # e.g. 1AbCdEf...
GOOGLE_SHEET_TAB_NAME = "Sheet1"                # change if needed

# Service account JSON file path (for Google Sheets API)
SERVICE_ACCOUNT_FILE = "/absolute/path/to/service_account.json"

# Optional: hard-code employee name instead of using the one from PDFs
EMPLOYEE_NAME_OVERRIDE = None  # e.g. "Yash Garg" or leave as None

# ============================================


def extract(pattern, text):
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_date(text):
    date_patterns = [
        (r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}", "%b %d, %Y"),
        (r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}", "%d %b %Y"),
        (r"\d{1,2}/\d{1,2}/\d{2,4}", None),
        (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
    ]

    for pattern, fmt in date_patterns:
        match = re.search(pattern, text)
        if not match:
            continue

        raw_date = match.group(0)

        try:
            if fmt:
                return datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
            else:
                # assume mm/dd/yy or mm/dd/yyyy
                parts = raw_date.split("/")
                if len(parts[2]) == 2:
                    raw_date = f"{parts[0]}/{parts[1]}/20{parts[2]}"
                return datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        except Exception:
            continue

    return None


def process_pdfs_from_folder(folder_path):
    rows = []
    for file_path in list_pdf_files(folder_path):
            try:
                print(f"Processing: {file_path}")
                text = extract_text_from_pdf(file_path)

                pdf_employee_name = (
                    extract(r"Thanks for riding,\s*(.+)", text)
                    or extract(r"Here's your receipt for your ride,\s*(.+)", text)
                )

                if EMPLOYEE_NAME_OVERRIDE and EMPLOYEE_NAME_OVERRIDE.strip():
                    final_employee_name = EMPLOYEE_NAME_OVERRIDE.strip()
                else:
                    final_employee_name = pdf_employee_name

                date = extract_date(text)
                total = extract(r"Total ₹([\d.]+)", text)

                rows.append(
                    {
                        "Employee Name": final_employee_name,
                        "Expense Vendor Name": "Uber",
                        "Expense Description": "uber booked for transportation between work and home",
                        "Date": date,
                        "Reference of Receipt (if applicable)": fname,
                        "Total (Please indicate if INR or USD in accounting format)": f"INR {total}" if total else None,
                    }
                )
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")

    df = pd.DataFrame(rows)
    print(f"Processed {len(df)} receipts")
    return df


def update_google_sheet(df):
    if df.empty:
        print("No data to write to Google Sheet. Exiting.")
        return

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(GOOGLE_SHEET_ID)
    worksheet = sheet.worksheet(GOOGLE_SHEET_TAB_NAME)

    # Clear existing data
    worksheet.clear()

    # Prepare data
    df_to_write = df.fillna("")  # avoid NAs in sheet
    data = [df_to_write.columns.tolist()] + df_to_write.values.tolist()

    # Update sheet
    worksheet.update("A1", data)
    print("Google Sheet updated successfully.")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-download", action="store_true", help="Skip downloading Drive folder (useful for testing)")
    parser.add_argument("--folder", type=str, help="Path to a local folder of PDFs (overrides download)")
    args = parser.parse_args()

    print("==== Uber Receipt Automation: START ====")

    if args.folder:
        folder_path = args.folder
        print(f"Using provided folder: {folder_path}")
    elif args.no_download:
        print("Skipping download (no-download flag set). Exiting.")
        return
    else:
        print(f"Downloading folder: {GDRIVE_FOLDER_URL}")
        folder_path = download_drive_folder(GDRIVE_FOLDER_URL)
        print(f"Downloaded to temp dir: {folder_path}")

    df = process_pdfs_from_folder(folder_path)
    update_google_sheet(df)

    print("==== Uber Receipt Automation: DONE ====")


if __name__ == "__main__":
    main()
