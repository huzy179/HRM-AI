from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import SessionDep
from backend.db import models
from backend.api import security

router = APIRouter()


class AuthRegisterIn(BaseModel):
    username: str
    password: str
    tenant_id: str = "default"


class AuthLoginIn(BaseModel):
    username: str
    password: str


class AuthTokenOut(BaseModel):
    access_token: str
    token_type: str
    username: str
    tenant_id: str


@router.post("/register")
def register(payload: AuthRegisterIn, session: SessionDep) -> dict:
    username = payload.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = session.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = security.hash_password(payload.password)
    user = models.User(
        username=username,
        hashed_password=hashed_pw,
        tenant_id=payload.tenant_id.strip() or "default",
        is_active=True,
        is_admin=False
    )
    session.add(user)
    session.commit()
    return {"ok": True, "message": "User registered successfully"}


@router.post("/login", response_model=AuthTokenOut)
def login(payload: AuthLoginIn, session: SessionDep) -> AuthTokenOut:
    user = session.query(models.User).filter(models.User.username == payload.username.strip()).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")

    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "role": "admin" if user.is_admin else "user"
    }
    token = security.create_access_token(token_data)
    return AuthTokenOut(
        access_token=token,
        token_type="bearer",
        username=user.username,
        tenant_id=user.tenant_id
    )
