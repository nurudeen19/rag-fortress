import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# Import models
from app.models.password_reset_token import PasswordResetToken

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./rag_fortress.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check_tokens():
    async with async_session() as session:
        # Get all tokens
        result = await session.execute(select(PasswordResetToken))
        tokens = result.scalars().all()
        
        print(f"Total tokens: {len(tokens)}\n")
        
        for token in tokens:
            now = datetime.now(timezone.utc)
            # Handle naive/aware comparison
            if token.expires_at.tzinfo is None:
                now = now.replace(tzinfo=None)
            
            is_expired = now > token.expires_at
            print(f"Token: {token.token[:20]}...")
            print(f"  Email: {token.email}")
            print(f"  Used: {token.is_used}")
            print(f"  Expires: {token.expires_at}")
            print(f"  Expired: {is_expired}")
            print(f"  Created: {token.created_at}\n")

asyncio.run(check_tokens())
