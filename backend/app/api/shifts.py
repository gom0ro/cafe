from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles, get_current_user

router = APIRouter()


@router.post("/open", response_model=schemas.ShiftOut)
async def open_shift(payload: schemas.ShiftOpen, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    return await crud.open_shift(db, current_user.id, payload)


@router.post("/close", response_model=schemas.ShiftOut)
async def close_shift(payload: schemas.ShiftClose, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    return await crud.close_shift(db, current_user.id, payload)


@router.get("/", response_model=list[schemas.ShiftOut])
async def list_shifts(db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    if current_user.role in ("admin", "owner"):
        return await crud.list_shifts(db)
    return await crud.list_shifts(db, user_id=current_user.id)


@router.get("/me/active", response_model=schemas.ShiftOut)
async def active_shift(db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    shift = await crud.active_shift_for_user(db, current_user.id)
    if not shift:
        return None
    return await crud._shift_out(db, shift)
