import pdfplumber
import pandas as pd
import re
import os

PDF_FOLDER = "./uber_receipts"
CSV_OUTPUT = "expense_report.csv"

def extract(pattern, text):
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None

rows = []

for filename in os.listdir(PDF_FOLDER):
    if not filename.lower().endswith(".pdf"):
        continue

    path = os.path.join(PDF_FOLDER, filename)

    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    employee_name = extract(r"Thanks for riding,\s*(.+)", text) or extract(r"Here's your receipt for your ride,\s*(.+)", text)
    date = extract(r"(Dec \d{1,2}, \d{4})", text)
    total = extract(r"Total ₹([\d.]+)", text)
    trip_type = extract(r"Trip details\s+(.+)", text)

    row = {
        "Employee Name": employee_name,
        "Expense Vendor Name": "Uber",
        "Expense Description": 'uber booked for transportation between work and home',
        "Date": date,
        "Reference of Receipt (if applicable)": filename,
        "Total (Please indicate if INR or USD in accounting format)": f"INR {total}"
    }

    rows.append(row)

df = pd.DataFrame(rows)
df.to_csv(CSV_OUTPUT, index=False)

print(f"Expense CSV generated: {CSV_OUTPUT}")
