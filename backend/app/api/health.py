from fastapi import APIRouter

router = APIRouter()


@router.get("/health/live")
async def health_live():
    return {"status": "ok"}

# --- Stage C addition ---
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Response
from app.db.session import get_db_session

@router.get("/health/ready")
async def health_ready(response: Response, db: AsyncSession = Depends(get_db_session)):
    try:
        await db.execute(sql_text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        response.status_code = 503
        return {"status": "unavailable"}