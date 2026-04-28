from __future__ import annotations
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.report_reasons_seed import seed_report_reasons_if_empty


async def main() -> None:
    async with AsyncSessionLocal() as db:
        inserted = await seed_report_reasons_if_empty(db)
    print(f"Inserted {inserted} report reasons.")


if __name__ == "__main__":
    asyncio.run(main())