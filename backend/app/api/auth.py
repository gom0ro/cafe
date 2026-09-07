from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app import crud, schemas

router = APIRouter()

logger = logging.getLogger("uvicorn.error")

SECRET_KEY = os.getenv("SECRET_KEY", "replace-me")
if SECRET_KEY == "replace-me":
    logger.warning("SECRET_KEY has the insecure default 'replace-me'. Set the SECRET_KEY env var in production.")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await crud.get_user_by_email(db, username)
    if not user:
        return False
    if not crud.verify_password(password, user.hashed_password):
        return False
    return user


@router.post("/signup", response_model=schemas.UserOut)
async def signup(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_session)):
    # Prevent privilege escalation via self-registration: only admins may assign
    # elevated roles through the /api/staff endpoints.
    user_in.role = "waiter"
    user = await crud.create_user(db, user_in)
    return user


class JSONLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str


@router.post("/login", response_model=schemas.Token)
async def login_json(credentials: JSONLogin, db: AsyncSession = Depends(get_session)):
    username = credentials.username or credentials.email
    if not username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username or email is required"
        )
    user = await authenticate_user(db, username, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_session)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await crud.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user


def require_roles(roles: list[str]):
    async def role_dependency(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return current_user
    return role_dependency
