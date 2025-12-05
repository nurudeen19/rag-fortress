import asyncio
from sqlalchemy import text
from app.core.database import get_async_engine

async def check_schema():
    engine = get_async_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'departments' 
            AND column_name IN ('created_at', 'updated_at')
        """))
        rows = result.fetchall()
        for row in rows:
            print(f'{row[0]}: {row[1]}')

asyncio.run(check_schema())
