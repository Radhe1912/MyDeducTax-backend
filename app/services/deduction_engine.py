from typing import Dict, List, Any


# =========================
# HELPERS
# =========================

def _sum_amounts(expenses: List[Dict]) -> float:
    return sum(float(e["amount"]) for e in expenses)


def _filter_expenses(expenses: List[Dict], rules: Dict) -> List[Dict]:
    result = expenses

    if "category" in rules:
        result = [e for e in result if e.get("category") in rules["category"]]

    if "sub_category_contains" in rules:
        result = [
            e for e in result
            if any(k in (e.get("sub_category") or "").lower() for k in rules["sub_category_contains"])
        ]

    return result


def _build_breakdown(expenses: List[Dict], allowed_total: float, reason: str) -> List[Dict]:
    remaining = allowed_total
    out = []

    for e in expenses:
        if remaining <= 0:
            break

        amt = float(e["amount"])
        applied = min(amt, remaining)

        out.append({
            "expense_id": e.get("id"),
            "amount": amt,
            "applied": applied,
            "reason": reason
        })

        remaining -= applied

    return out


# =========================
# RULE HANDLERS
# =========================

def _handle_capped(expenses: List[Dict], rules: Dict):
    filtered = _filter_expenses(expenses, rules)

    total = _sum_amounts(filtered)
    max_limit = float(rules.get("max_limit", total))

    allowed = min(total, max_limit)

    return total, allowed, max_limit, filtered


def _handle_percentage(expenses: List[Dict], rules: Dict):
    filtered = _filter_expenses(expenses, rules)

    total = _sum_amounts(filtered)
    pct = float(rules.get("percentage", 1))

    allowed = total * pct

    return total, allowed, None, filtered


def _handle_split(expenses: List[Dict], rules: Dict, context: Dict):
    filtered = _filter_expenses(expenses, rules)

    is_senior_self = context.get("is_senior_self", False)
    is_senior_parents = context.get("is_senior_parents", False)

    self_limit = rules.get("senior_self_limit") if is_senior_self else rules.get("self_limit")
    parent_limit = rules.get("senior_parent_limit") if is_senior_parents else rules.get("parent_limit")

    self_exp = [e for e in filtered if "parent" not in (e.get("sub_category") or "").lower()]
    parent_exp = [e for e in filtered if "parent" in (e.get("sub_category") or "").lower()]

    self_total = _sum_amounts(self_exp)
    parent_total = _sum_amounts(parent_exp)

    self_allowed = min(self_total, self_limit)
    parent_allowed = min(parent_total, parent_limit)

    total = self_total + parent_total
    allowed = self_allowed + parent_allowed
    max_limit = (self_limit + parent_limit)

    return total, allowed, max_limit, filtered


def _handle_formula(expenses: List[Dict], rules: Dict, context: Dict):
    formula = rules.get("formula")

    # =========================
    # HRA FORMULA
    # =========================
    if formula == "hra":
        salary = context.get("salary", 0)
        hra_received = context.get("hra_received", 0)
        is_metro = context.get("is_metro", True)

        rent_paid = _sum_amounts([e for e in expenses if e.get("category") == "rent"])

        if salary <= 0 or hra_received <= 0 or rent_paid <= 0:
            return rent_paid, 0, None, []

        percent_salary = 0.5 if is_metro else 0.4

        allowed = min(
            hra_received,
            salary * percent_salary,
            max(rent_paid - (0.1 * salary), 0)
        )

        return rent_paid, allowed, None, expenses

    return 0, 0, None, []


# =========================
# MAIN ENGINE (FULLY DYNAMIC)
# =========================

async def compute_deductions(
    expense_section_map: Dict[str, List[Dict]],
    sections,
    context: Dict = {}
) -> List[Dict]:

    results = []

    for section in sections:
        rules = section.rules or {}
        section_code = section.section_code

        expenses = expense_section_map.get(section_code, [])

        if not rules:
            continue

        rule_type = rules.get("type")

        if rule_type == "capped":
            total, allowed, max_limit, filtered = _handle_capped(expenses, rules)

        elif rule_type == "percentage":
            total, allowed, max_limit, filtered = _handle_percentage(expenses, rules)

        elif rule_type == "split":
            total, allowed, max_limit, filtered = _handle_split(expenses, rules, context)

        elif rule_type == "formula":
            total, allowed, max_limit, filtered = _handle_formula(expenses, rules, context)

        else:
            continue

        results.append({
            "section_code": section_code,
            "total_claimed": total,
            "total_allowed": allowed,
            "remaining_limit": (max_limit - allowed) if max_limit else None,
            "breakdown": _build_breakdown(filtered, allowed, f"Rule-based ({rule_type})")
        })

    return results