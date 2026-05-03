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


def classify_expense(expense: Dict) -> Dict:
    """
    Input: raw expense dict
    Output: enriched expense with category + sub_category
    """

    description = normalize_text(expense.get("description", ""))

    category = "other"

    for cat, patterns in CATEGORY_RULES.items():
        for pattern in patterns:
            if re.search(pattern, description):
                category = cat
                break
        if category != "other":
            break

    expense["category"] = category
    expense["sub_category"] = description[:50] if description else None
    expense["txn_hash"] = generate_txn_hash(expense)

    return expense

def generate_txn_hash(expense: dict) -> str:
    key = f"{expense.get('description','')}-{expense.get('amount')}-{expense.get('transaction_date')}"
    return hashlib.md5(key.encode()).hexdigest()