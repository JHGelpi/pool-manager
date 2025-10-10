from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.config import settings


async def get_current_user(db: AsyncSession = Depends(get_db)) -> User:
    """
    Get the current user. 
    For now, returns the default user from settings.
    In production, this would validate a JWT token.
    """
    result = await db.execute(
        select(User).where(User.email == settings.DEFAULT_USER_EMAIL)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Default user {settings.DEFAULT_USER_EMAIL} not found. Please run migrations."
        )
    
    return user