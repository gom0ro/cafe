from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=schemas.StaffProfileOut)
async def read_my_profile(db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    profile = await crud.get_profile_by_user_id(db, current_user.id)
    data = await crud.profile_to_dict(profile)
    data["full_name"] = current_user.full_name
    return data


@router.put("/me", response_model=schemas.StaffProfileOut)
async def update_my_profile(payload: schemas.StaffProfileUpdate, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    profile = await crud.update_profile(db, current_user.id, payload)
    data = await crud.profile_to_dict(profile)
    data["full_name"] = current_user.full_name if payload.full_name is None else payload.full_name
    return data


@router.patch("/me/socials", response_model=schemas.StaffProfileOut)
async def update_my_socials(payload: schemas.SocialLinks, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    profile = await crud.merge_social_links(db, current_user.id, payload.dict())
    data = await crud.profile_to_dict(profile)
    data["full_name"] = current_user.full_name
    return data


@router.patch("/me/dashboard", response_model=schemas.StaffProfileOut)
async def update_my_dashboard(payload: schemas.DashboardPreferences, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    profile = await crud.merge_dashboard_preferences(db, current_user.id, payload.dict())
    data = await crud.profile_to_dict(profile)
    data["full_name"] = current_user.full_name
    return data
