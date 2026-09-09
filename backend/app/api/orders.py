from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles, get_current_user

router = APIRouter()


@router.post("/", response_model=schemas.OrderOut)
async def create_order(order: schemas.OrderCreate, db: AsyncSession = Depends(get_session), current_user=Depends(require_roles(["cashier", "waiter", "admin"]))):
    return await crud.create_order(db, order, user_id=current_user.id)


@router.get("/", response_model=list[schemas.OrderOut])
async def list_orders(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Статусы через запятую, напр. new,kitchen,ready"),
    table_id: Optional[int] = Query(None, description="Только заказы по конкретному столику"),
    db: AsyncSession = Depends(get_session),
    _=Depends(require_roles(["cashier", "waiter", "admin", "chef"]))):
    statuses = [s.strip() for s in status.split(",") if s.strip()] if status else None
    return await crud.list_orders(db, limit=limit, offset=offset, statuses=statuses, table_id=table_id)


@router.get("/{order_id}", response_model=schemas.OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["cashier", "waiter", "admin", "chef"]))):
    order = await crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
async def update_status(order_id: int, payload: schemas.OrderStatusUpdate, db: AsyncSession = Depends(get_session), current_user=Depends(require_roles(["cashier", "waiter", "admin", "chef"]))):
    order = await crud.update_order_status(db, order_id, payload.status, payload.payment_method, actor_id=current_user.id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
