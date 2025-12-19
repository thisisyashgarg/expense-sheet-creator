import os
import re
import tempfile
from datetime import datetime

import gdown
import pdfplumber


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
        use_cookies=False,
    )
    return temp_dir


def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def list_pdf_files(folder_path):
    pdfs = []
    for root, _, files in os.walk(folder_path):
        for fname in files:
            if fname.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, fname))
    return pdfs
