import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime
import gdown
import tempfile
import os

st.set_page_config(
    page_title="Uber Receipt → Expense CSV",
    layout="centered"
)

st.title("Uber Receipt → Expense CSV")
st.write(
    "Upload Uber receipt PDFs **or** paste a Google Drive folder link "
    "to generate a consolidated expense CSV."
)

# ---------------- Utility Functions ---------------- #

def extract(pattern, text):
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_date(text):
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
                parts = raw_date.split("/")
                if len(parts[2]) == 2:
                    raw_date = f"{parts[0]}/{parts[1]}/20{parts[2]}"
                return datetime.strptime(raw_date, "%m/%d/%Y").strftime("%Y-%m-%d")
        except Exception:
            continue

    return None


def download_drive_folder(folder_url):
    temp_dir = tempfile.mkdtemp()
    gdown.download_folder(
        url=folder_url,
        output=temp_dir,
        quiet=True,
        use_cookies=False
    )
    return temp_dir


def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


# ---------------- UI ---------------- #

source = st.radio(
    "Choose input source",
    ["Upload PDFs", "Google Drive Folder"]
)

pdf_files = []

if source == "Upload PDFs":
    uploaded_files = st.file_uploader(
        "Upload Uber receipt PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )
    pdf_files = uploaded_files or []

elif source == "Google Drive Folder":
    folder_url = st.text_input(
        "Paste Google Drive folder link (set to 'Anyone with link → Viewer')"
    )

    if folder_url:
        with st.spinner("Downloading PDFs from Google Drive..."):
            folder_path = download_drive_folder(folder_url)
            pdf_files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith(".pdf")
            ]

# ---------------- Processing ---------------- #

if pdf_files:
    rows = []

    for file in pdf_files:
        try:
            text = extract_text_from_pdf(file)

            employee_name = (
                extract(r"Thanks for riding,\s*(.+)", text)
                or extract(r"Here's your receipt for your ride,\s*(.+)", text)
            )

            date = extract_date(text)
            total = extract(r"Total ₹([\d.]+)", text)

            file_name = file.name if hasattr(file, "name") else os.path.basename(file)

            rows.append({
                "Employee Name": employee_name,
                "Expense Vendor Name": "Uber",
                "Expense Description": "uber booked for transportation between work and home",
                "Date": date,
                "Reference of Receipt (if applicable)": file_name,
                "Total (Please indicate if INR or USD in accounting format)": f"INR {total}" if total else None
            })

        except Exception as e:
            st.warning(f"Failed to process {file}: {e}")

    df = pd.DataFrame(rows)

    st.success(f"Processed {len(df)} receipts")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Expense CSV",
        data=csv,
        file_name="expense_report.csv",
        mime="text/csv"
    )
