import asyncio
from sqlalchemy import text
from app.core.database import DatabaseManager
from app.config.database_settings import DatabaseSettings

async def check_schema():
    db_settings = DatabaseSettings()
    manager = DatabaseManager(db_settings)
    engine = await manager.create_async_engine()
    
    async with engine.connect() as conn:
        print("Checking file_uploads columns:")
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'file_uploads' 
            AND column_name IN ('created_at', 'updated_at', 'approved_at')
        """))
        rows = result.fetchall()
        for row in rows:
            print(f'{row[0]}: {row[1]}')

asyncio.run(check_schema())
