import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

st.set_page_config(page_title="Uber Receipt to CSV", layout="centered")

st.title("Uber Receipt → Expense CSV")
st.write("Upload multiple Uber receipt PDFs and download a consolidated expense CSV.")

def extract(pattern, text):
    match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_date(text):
    date_patterns = [
        (r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}", "%b %d, %Y"),
        (r"\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}", "%d %b %Y"),
        (r"\d{1,2}/\d{1,2}/\d{2,4}", None),
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


uploaded_files = st.file_uploader(
    "Upload Uber receipt PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    rows = []

    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        employee_name = (
            extract(r"Thanks for riding,\s*(.+)", text)
            or extract(r"Here's your receipt for your ride,\s*(.+)", text)
        )

        date = extract_date(text)
        total = extract(r"Total ₹([\d.]+)", text)

        rows.append({
            "Employee Name": employee_name,
            "Expense Vendor Name": "Uber",
            "Expense Description": "uber booked for transportation between work and home",
            "Date": date,
            "Reference of Receipt (if applicable)": file.name,
            "Total (Please indicate if INR or USD in accounting format)": f"INR {total}" if total else None
        })

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
