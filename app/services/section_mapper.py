from typing import List, Dict
import json


def normalize(val):
    if not val:
        return ""
    return str(val).strip().lower()


def parse_rules(rules_metadata):
    if not rules_metadata:
        return {}

    # if already dict → return
    if isinstance(rules_metadata, dict):
        return rules_metadata

    # if string → parse
    try:
        return json.loads(rules_metadata)
    except Exception:
        return {}

def matches_section(expense: Dict, section) -> bool:
    rules = parse_rules(section.rules_metadata)

    if not rules:
        return False

    exp_cat = normalize(expense.get("category"))
    exp_sub = normalize(expense.get("sub_category"))
    desc = normalize(expense.get("description"))

    allowed_categories = rules.get("allowed_categories", [])
    if allowed_categories:
        if exp_cat not in [normalize(c) for c in allowed_categories]:
            return False

    allowed_sub = rules.get("sub_category", [])
    if allowed_sub:
        if not any(sub in exp_sub for sub in [normalize(s) for s in allowed_sub]):
            return False

    excluded_sub = rules.get("exclude_sub_category", [])
    if excluded_sub:
        if any(sub in exp_sub for sub in [normalize(s) for s in excluded_sub]):
            return False

    keywords = rules.get("keywords", [])
    if keywords:
        if not any(k in desc for k in [normalize(k) for k in keywords]):
            return False

    return True

def map_expenses_to_sections(
    expenses: List[Dict],
    sections
) -> Dict[str, List[Dict]]:

    mapping = {}

    for section in sections:
        section_code = section.section_code
        mapping[section_code] = []

        for exp in expenses:
            if matches_section(exp, section):
                mapping[section_code].append(exp)

    # remove empty sections
    return {k: v for k, v in mapping.items() if v}