from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.models.tax_section import TaxSection

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_tax_sections():
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(TaxSection))
        if existing.scalars().first():
            return  # already seeded

        sections = [
            TaxSection(
                section_code="80C",
                name="Investments",
                max_limit=150000,
                rule_type="AGGREGATE",
                rules_metadata={
                    "allowed_categories": [
                        "investment",
                        "ppf",
                        "lic",
                        "elss"
                    ]
                },
                rules={
                    "type": "capped",
                    "max_limit": 150000,
                    "category": ["investment", "ppf", "lic", "elss"]
                }
            ),
            TaxSection(
                section_code="80D",
                name="Health Insurance",
                max_limit=25000,
                rule_type="AGGREGATE",
                rules_metadata={
                    "allowed_categories": ["insurance"]
                },
                rules={
                    "type": "capped",
                    "max_limit": 25000,
                    "category": ["insurance"]
                }
            ),
            TaxSection(
                section_code="HRA",
                name="House Rent Allowance",
                max_limit=None,
                rule_type="FORMULA",
                rules_metadata={
                    "requires": ["salary", "rent"]
                },
                rules={
                    "type": "formula",
                    "formula": "hra"
                }
            ),
        ]

        session.add_all(sections)
        await session.commit()

async def init_db():
    await create_tables()
    await seed_tax_sections()