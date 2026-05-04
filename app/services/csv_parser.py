import pandas as pd
from typing import List, Dict, Optional
import re
from datetime import datetime
import hashlib


COLUMN_ALIASES = {
    "date": ["date", "txn date", "transaction date", "value date"],
    "description": ["description", "narration", "remarks", "details"],
    "debit": ["debit", "withdrawal", "dr"],
    "credit": ["credit", "deposit", "cr"],
    "amount": ["amount", "txn amount"]
}


# =========================
# COLUMN NORMALIZATION
# =========================
def normalize_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    mapping = {k: None for k in COLUMN_ALIASES}

    for col in columns:
        col_clean = col.lower().strip()

        for key, aliases in COLUMN_ALIASES.items():
            if any(alias in col_clean for alias in aliases):
                mapping[key] = col

    return mapping


# =========================
# CLEANERS
# =========================
def clean_text(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.strip())


def parse_date(value):
    try:
        return pd.to_datetime(value, dayfirst=True)
    except Exception:
        return None


def parse_amount(row, mapping):
    try:
        if mapping["amount"]:
            return float(row[mapping["amount"]])

        debit = row.get(mapping["debit"])
        credit = row.get(mapping["credit"])

        if pd.notna(debit):
            return float(debit)
        if pd.notna(credit):
            return 0  # skip income

        return 0
    except:
        return 0


# =========================
# HASH FOR DEDUPLICATION
# =========================
def generate_txn_hash(description, amount, date):
    raw = f"{description}-{amount}-{date}"
    return hashlib.sha256(raw.encode()).hexdigest()


# =========================
# CORE TRANSFORM
# =========================
def transform_df(df: pd.DataFrame) -> List[Dict]:
    mapping = normalize_columns(df.columns)

    parsed = []

    for _, row in df.iterrows():
        amount = parse_amount(row, mapping)

        if amount <= 0:
            continue

        desc = clean_text(row.get(mapping["description"], ""))
        date = parse_date(row.get(mapping["date"]))

        txn_hash = generate_txn_hash(desc, amount, date)

        parsed.append({
            "description": desc,
            "amount": float(amount),
            "transaction_date": date,
            "txn_hash": txn_hash,
            "raw_data": row.to_dict(),
            "source": "upload"
        })

    return parsed


# =========================
# ENTRY FUNCTION
# =========================
async def parse_file(file) -> List[Dict]:
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        df = pd.read_csv(file.file)

    elif filename.endswith(".xlsx"):
        df = pd.read_excel(file.file)

    else:
        raise ValueError("Unsupported file format")

    if df.empty:
        return []

    return transform_df(df)