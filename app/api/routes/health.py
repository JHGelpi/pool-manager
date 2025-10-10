from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "ok"}


@router.get("/readyz")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Check if app is ready (database connection)"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}
