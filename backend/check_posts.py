import asyncio
from sqlalchemy import text
from app.db.session import engine

IDS = "('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb005','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbb006')"

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text(f"select * from posts where id in {IDS}"))
        rows = result.mappings().all()
        print(len(rows), "rows")
        for r in rows:
            print(dict(r))
    await engine.dispose()

asyncio.run(main())