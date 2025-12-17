import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime

PDF_FOLDER = "./uber_receipts"
CSV_OUTPUT = "expense_report.csv"


def extract(pattern, text):
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_date(text):
    """
    Extracts a date from Uber receipts with multiple possible formats
    and normalizes it to YYYY-MM-DD.
    """

    date_patterns = [
        # Dec 16, 2025 / December 16, 2025
        (r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}", "%b %d, %Y"),

        # 16 Dec 2025
        (r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}", "%d %b %Y"),

        # 12/16/25 or 12/16/2025
        (r"\d{1,2}/\d{1,2}/\d{2,4}", None),

        # 2025-12-16
        (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d")
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
                # Handle MM/DD/YY vs MM/DD/YYYY
                parts = raw_date.split("/")
                if len(parts[2]) == 2:
                    raw_date = f"{parts[0]}/{parts[1]}/20{parts[2]}"
                return datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        except Exception:
            continue

    return None


rows = []

for filename in os.listdir(PDF_FOLDER):
    if not filename.lower().endswith(".pdf"):
        continue

    file_path = os.path.join(PDF_FOLDER, filename)

    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    employee_name = (
        extract(r"Thanks for riding,\s*(.+)", text)
        or extract(r"Here's your receipt for your ride,\s*(.+)", text)
    )

    date = extract_date(text)
    total = extract(r"Total ₹([\d.]+)", text)

    row = {
        "Employee Name": employee_name,
        "Expense Vendor Name": "Uber",
        "Expense Description": "uber booked for transportation between work and home",
        "Date": date,
        "Reference of Receipt (if applicable)": filename,
        "Total (Please indicate if INR or USD in accounting format)": f"INR {total}" if total else None
    }

    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(CSV_OUTPUT, index=False)

print(f"Expense CSV generated successfully → {CSV_OUTPUT}")
