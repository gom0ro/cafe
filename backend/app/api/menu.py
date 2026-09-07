from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles
import aiofiles
import os
import uuid

router = APIRouter()


@router.get("/", response_model=list[schemas.MenuItemOut])
async def list_menu(db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter", "chef"]))):
    return await crud.list_menu_items(db)


@router.post("/", response_model=schemas.MenuItemOut)
async def create_menu(
    name: str = Form(...),
    price: float = Form(...),
    category: str | None = Form(None),
    description: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_session),
    _=Depends(require_roles(["admin", "cashier", "waiter"]))
):
    image_path = None
    if image:
        os.makedirs('uploads', exist_ok=True)
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join('uploads', filename)
        async with aiofiles.open(path, 'wb') as out:
            content = await image.read()
            await out.write(content)
        image_path = f"/uploads/{filename}"

    item_in = schemas.MenuItemCreate(name=name, price=price, category=category, description=description, image=image_path)
    return await crud.create_menu_item(db, item_in, image_path=image_path)


@router.put("/{item_id}", response_model=schemas.MenuItemOut)
async def update_menu(
    item_id: int,
    name: str | None = Form(None),
    price: float | None = Form(None),
    category: str | None = Form(None),
    description: str | None = Form(None),
    available: bool | None = Form(None),
    image: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_session),
    _=Depends(require_roles(["admin", "cashier", "waiter"]))
):
    image_path = None
    if image and image.filename:
        os.makedirs('uploads', exist_ok=True)
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join('uploads', filename)
        async with aiofiles.open(path, 'wb') as out:
            content = await image.read()
            await out.write(content)
        image_path = f"/uploads/{filename}"

    item_in = schemas.MenuItemUpdate(name=name, price=price, category=category, description=description, available=available, image=image_path)
    db_item = await crud.update_menu_item(db, item_id, item_in, image_path=image_path)
    if not db_item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    return db_item


@router.delete("/{item_id}")
async def delete_menu(item_id: int, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "cashier", "waiter"]))):
    deleted = await crud.delete_menu_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    return {"ok": True}
