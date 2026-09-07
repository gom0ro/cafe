from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=list[schemas.TableOut])
async def list_tables(db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter", "chef"]))):
    return await crud.list_tables(db)


@router.post("/", response_model=schemas.TableOut)
async def create_table(table: schemas.TableCreate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin"]))):
    return await crud.create_table(db, table)


@router.patch("/{table_id}", response_model=schemas.TableOut)
async def update_table(table_id: int, patch: schemas.TableUpdate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin"]))):
    table = await crud.update_table(db, table_id, patch)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


@router.delete("/{table_id}")
async def delete_table(table_id: int, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin"]))):
    ok = await crud.delete_table(db, table_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Table not found")
    return {"ok": True}
