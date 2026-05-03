import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import re


# =========================
# COLUMN ALIASES (extendable)
# =========================
COLUMN_ALIASES = {
    "date": ["date", "txn date", "transaction date", "value date"],
    "description": ["description", "narration", "remarks", "details"],
    "debit": ["debit", "withdrawal", "dr"],
    "credit": ["credit", "deposit", "cr"],
    "amount": ["amount", "txn amount"]
}


def normalize_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    mapping = {k: None for k in COLUMN_ALIASES}

    lower_cols = [c.lower().strip() for c in columns]

    for key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            for col in lower_cols:
                if alias in col:
                    mapping[key] = col
                    break

    return mapping


def parse_amount(row, mapping):
    if mapping["amount"]:
        return float(row[mapping["amount"]])

    debit = row.get(mapping["debit"])
    credit = row.get(mapping["credit"])

    if pd.notna(debit):
        return -float(debit)
    if pd.notna(credit):
        return float(credit)

    return 0.0


def parse_date(value):
    try:
        return pd.to_datetime(value, dayfirst=True)
    except Exception:
        return None


def clean_text(text):
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", text.strip())


# =========================
# MAIN PARSER
# =========================
def parse_csv(file) -> List[Dict]:
    df = pd.read_csv(file)

    df.columns = [c.lower().strip() for c in df.columns]

    mapping = normalize_columns(df.columns)

    parsed = []

    for _, row in df.iterrows():
        amount = parse_amount(row, mapping)

        if amount == 0:
            continue

        parsed.append({
            "description": clean_text(row.get(mapping["description"], "")),
            "amount": abs(amount),  # keep positive for deduction logic
            "transaction_date": parse_date(row.get(mapping["date"])),
            "raw_data": row.to_dict(),
            "source": "csv"
        })

    return parsed