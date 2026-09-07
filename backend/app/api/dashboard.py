from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud
from app.api.auth import require_roles

router = APIRouter()


@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter", "chef"]))):
    return await crud.get_dashboard_stats(db)
