import streamlit as st
import pandas as pd
import os

from utils import (
    extract,
    extract_date,
    download_drive_folder,
    extract_text_from_pdf,
)

st.set_page_config(
    page_title="Uber Receipt → Expense CSV",
    layout="centered"
)

st.title("Uber Receipt → Expense CSV")

st.write(
    "Upload Uber receipt PDFs **or** paste a Google Drive folder link "
    "to generate a consolidated expense CSV."
)

# ---------------- Employee Name Input ---------------- #

employee_name_input = st.text_input(
    "Employee Name (optional)",
    placeholder="Leave empty to use name from receipt PDFs"
)

# ---------------- Utility Functions ---------------- #


# NOTE:
# Google Drive folders MUST be shared as:
# "Anyone with the link" → "Viewer"
# Otherwise, gdown will NOT be able to download the files.
# utilities `extract`, `extract_date`, `download_drive_folder`, and `extract_text_from_pdf`
# are provided by utils.py


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
    st.info(
        "📁 Google Drive folder must be shared as "
        "**Anyone with the link → Viewer** for this to work."
    )

    folder_url = st.text_input("Paste Google Drive folder link")

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

            pdf_employee_name = (
                extract(r"Thanks for riding,\s*(.+)", text)
                or extract(r"Here's your receipt for your ride,\s*(.+)", text)
            )

            final_employee_name = (
                employee_name_input.strip()
                if employee_name_input.strip()
                else pdf_employee_name
            )

            date = extract_date(text)
            total = extract(r"Total ₹([\d.]+)", text)

            file_name = file.name if hasattr(file, "name") else os.path.basename(file)

            rows.append({
                "Employee Name": final_employee_name,
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
