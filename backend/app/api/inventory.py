from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import require_roles

router = APIRouter()


@router.get("/", response_model=list[schemas.IngredientOut])
async def list_ingredients(db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "chef"]))):
    return await crud.list_ingredients(db)


@router.post("/", response_model=schemas.IngredientOut)
async def create_ingredient(ing: schemas.IngredientCreate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "chef"]))):
    return await crud.create_ingredient(db, ing)


@router.put("/{ing_id}", response_model=schemas.IngredientOut)
async def update_ingredient(ing_id: int, patch: schemas.IngredientUpdate, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "chef"]))):
    ing = await crud.update_ingredient(db, ing_id, patch)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ing


@router.delete("/{ing_id}")
async def delete_ingredient(ing_id: int, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "chef"]))):
    deleted = await crud.delete_ingredient(db, ing_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"ok": True}


@router.patch("/{ing_id}/adjust", response_model=schemas.IngredientOut)
async def adjust_quantity(ing_id: int, delta: float, db: AsyncSession = Depends(get_session), _=Depends(require_roles(["admin", "chef"]))):
    ing = await crud.adjust_ingredient_quantity(db, ing_id, delta)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return ing
