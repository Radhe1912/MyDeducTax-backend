import re
from typing import Dict
import hashlib

CATEGORY_RULES = {
    "insurance": [r"insurance", r"policy", r"mediclaim"],
    "investment": [r"ppf", r"elss", r"mutual fund", r"lic"],
    "rent": [r"rent", r"house rent"],
    "salary": [r"salary", r"payroll"],
    "loan": [r"loan", r"emi"],
}


def normalize_text(text: str) -> str:
    return text.lower().strip() if text else ""

def classify_expense(expense: dict) -> dict:
    desc = expense.get("description", "").lower()

    if "lic" in desc or "ppf" in desc or "elss" in desc:
        expense["category"] = "investment"
        expense["sub_category"] = "80c"

    elif "nps" in desc:
        expense["category"] = "investment"
        expense["sub_category"] = "nps"

    elif "insurance" in desc:
        expense["category"] = "insurance"
        expense["sub_category"] = "80d"

    elif "rent" in desc:
        expense["category"] = "rent"
        expense["sub_category"] = "hra"

    elif "donation" in desc or "ngo" in desc:
        expense["category"] = "donation"
        expense["sub_category"] = "80g"

    else:
        expense["category"] = "other"
        expense["sub_category"] = "misc"

    return expense

def generate_txn_hash(expense: dict) -> str:
    key = f"{expense.get('description','')}-{expense.get('amount')}-{expense.get('transaction_date')}"
    return hashlib.md5(key.encode()).hexdigest()