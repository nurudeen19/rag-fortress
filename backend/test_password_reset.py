import asyncio
from app.services.user.password_service import PasswordService
from app.core.database import get_async_session

async def test_reset():
    async with get_async_session()() as session:
        password_service = PasswordService(session)
        
        # Create a reset token
        token, error = await password_service.create_reset_token(user_id=1)
        print(f"Token created: {token}")
        print(f"Error: {error}")
        
        if token:
            # Verify token
            user_id, error = await password_service.verify_reset_token(token=token, email="admin@ragfortress.com")
            print(f"Token verified for user: {user_id}")
            print(f"Error: {error}")

asyncio.run(test_reset())
