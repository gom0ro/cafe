from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=list[schemas.UserOut])
async def list_staff(db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin"]))):
    return await crud.list_users(db)


@router.post("/", response_model=schemas.UserOut)
async def create_staff(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin"]))):
    user = await crud.create_user(db, user_in)
    return user


@router.put("/{user_id}", response_model=schemas.UserOut)
async def update_staff(user_id: int, patch: schemas.UserUpdate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin"]))):
    user = await crud.update_user(db, user_id, patch)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return user


@router.delete("/{user_id}")
async def delete_staff(user_id: int, db: AsyncSession = Depends(get_session), current_user=Depends(require_roles(["admin"]))):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Нельзя удалить собственную учётную запись")
    deleted = await crud.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    return {"ok": True}
