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

async def compute_deductions(expense_map, sections, context={}):
    results = []
    total = 0

    for section in sections:
        code = section.section_code

        if code not in expense_map:
            continue

        expenses = expense_map[code]

        # =========================
        # FORMULA BASED (HRA)
        # =========================
        if section.rule_type == "FORMULA":
            if code == "HRA":
                rent = sum(e["amount"] for e in expenses)
                salary = context.get("salary", 0)
                hra_received = context.get("hra_received", 0)

                if salary > 0 and hra_received > 0:
                    section_total = min(
                        max(rent - (0.1 * salary), 0),
                        0.4 * salary,
                        hra_received
                    )
                else:
                    section_total = 0
            else:
                section_total = 0

        else:
            # =========================
            # NORMAL AGGREGATE
            # =========================
            raw_total = sum(e["amount"] for e in expenses)

            if section.max_limit:
                section_total = min(raw_total, float(section.max_limit))
                remaining = float(section.max_limit) - section_total
                limit = float(section.max_limit)
            else:
                section_total = raw_total
                remaining = None
                limit = None

        # =========================
        # ADD RESULT (ONLY ONCE)
        # =========================
        if section_total > 0:
            results.append({
                "section": code,
                "amount": section_total,
                "count": len(expenses),
                "limit": limit,
                "remaining": remaining
            })

            total += section_total

    return {
        "total_sections": len(results),
        "total_deduction": total,
        "deductions": results
    }