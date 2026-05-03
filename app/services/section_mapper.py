from typing import List, Dict
from sqlalchemy import select
from app.models.tax_section import TaxSection


async def load_tax_sections(db):
    result = await db.execute(select(TaxSection))
    return result.scalars().all()

def match_section(expense, section) -> bool:
    metadata = section.rules_metadata or {}

    allowed_categories = metadata.get("allowed_categories", [])

    if expense["category"] in allowed_categories:
        return True

    return False


async def map_expenses_to_sections(expenses: List[Dict], db):
    sections = await load_tax_sections(db)

    mapping = {}

    for section in sections:
        mapping[section.section_code] = []

    for expense in expenses:
        for section in sections:
            if match_section(expense, section):
                mapping[section.section_code].append(expense)

    return mapping