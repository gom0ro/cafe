from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles

router = APIRouter()


@router.get("/", response_model=list[schemas.TableBookingOut])
async def list_bookings(
    upcoming: bool = Query(False, description="Только будущие брони"),
    db: AsyncSession = Depends(get_session),
    _=Depends(require_roles(["admin", "cashier", "waiter"])),
):
    return await crud.list_bookings(db, upcoming_only=upcoming)


@router.post("/", response_model=schemas.TableBookingOut)
async def create_booking(payload: schemas.TableBookingCreate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter"]))):
    return await crud.create_table_booking(db, payload)


@router.patch("/{booking_id}", response_model=schemas.TableBookingOut)
async def update_booking(booking_id: int, patch: schemas.TableBookingUpdate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter"]))):
    booking = await crud.update_table_booking(db, booking_id, patch)
    if not booking:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    return booking


@router.delete("/{booking_id}")
async def delete_booking(booking_id: int, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter"]))):
    ok = await crud.delete_table_booking(db, booking_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Бронь не найдена")
    return {"ok": True}