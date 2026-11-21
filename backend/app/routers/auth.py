from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hmac
import re
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.app.core.config import COOKIE_NAME, CSRF_COOKIE_NAME, COOKIE_SECURE, SESSION_DAYS
from backend.app.core.dependencies import get_current_user, verify_user_csrf
from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, new_session_token, hash_session_token
from backend.app.models.entities import User, UserSession

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class RegisterInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name is required")
        return value

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,50}", value):
            raise ValueError("Username must be 3–50 characters and use only lowercase letters, numbers, and underscores")
        return value


class UserProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    username: str = Field(min_length=3, max_length=50)
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("name")
    @classmethod
    def clean_profile_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name is required")
        return value

    @field_validator("username")
    @classmethod
    def clean_profile_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,50}", value):
            raise ValueError("Username must be 3–50 characters and use only lowercase letters, numbers, and underscores")
        return value


class LoginInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        return value.strip().lower()


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    max_age = SESSION_DAYS * 24 * 60 * 60
    response.set_cookie(key=COOKIE_NAME, value=session_token, max_age=max_age, httponly=True,
                        secure=COOKIE_SECURE, samesite="lax", path="/")
    response.set_cookie(key=CSRF_COOKIE_NAME, value=csrf_token, max_age=max_age, httponly=False,
                        secure=COOKIE_SECURE, samesite="lax", path="/")


def _verify_pre_auth_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed. Refresh the page and try again.")


def _user_payload(user: User) -> dict:
    return {"id": user.id, "name": user.name, "username": user.username, "theme": user.theme}


@router.get("/csrf")
def get_csrf_token(response: Response):
    token = secrets.token_urlsafe(32)
    response.set_cookie(key=CSRF_COOKIE_NAME, value=token, max_age=7200, httponly=False,
                        secure=COOKIE_SECURE, samesite="lax", path="/")
    return {"csrf_token": token}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, response: Response, request: Request, db: Session = Depends(get_db)):
    _verify_pre_auth_csrf(request)
    exists = db.scalar(select(User.id).where(User.username == payload.username))
    if exists:
        raise HTTPException(status_code=409, detail="This username is already registered")
    user = User(name=payload.name, username=payload.username, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    session_token = new_session_token()
    csrf_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    db.add(UserSession(user_id=user.id, token_hash=hash_session_token(session_token),
                       csrf_token_hash=hash_session_token(csrf_token), expires_at=expires_at))
    db.commit()
    db.refresh(user)
    _set_auth_cookies(response, session_token, csrf_token)
    return {"user": _user_payload(user)}


@router.post("/login")
def login(payload: LoginInput, response: Response, request: Request, db: Session = Depends(get_db)):
    _verify_pre_auth_csrf(request)
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.is_active or user.deleted_at is not None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username or password is incorrect")
    now = datetime.now(timezone.utc)
    db.execute(delete(UserSession).where(UserSession.expires_at < now))
    session_token = new_session_token()
    csrf_token = secrets.token_urlsafe(32)
    db.add(UserSession(user_id=user.id, token_hash=hash_session_token(session_token),
                       csrf_token_hash=hash_session_token(csrf_token), expires_at=now + timedelta(days=SESSION_DAYS)))
    db.commit()
    _set_auth_cookies(response, session_token, csrf_token)
    return {"user": _user_payload(user)}


@router.post("/logout")
def logout(request: Request, response: Response, user: User = Depends(get_current_user),
           _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == hash_session_token(token)))
        db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/", secure=COOKIE_SECURE, httponly=False, samesite="lax")
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"user": _user_payload(user)}


@router.patch("/profile")
def update_profile(
    payload: UserProfileInput,
    request: Request,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(verify_user_csrf),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(User).where(User.username == payload.username, User.id != user.id))
    if existing:
        raise HTTPException(status_code=409, detail="This username is already in use")

    if payload.new_password:
        if not payload.current_password or not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.password_hash = hash_password(payload.new_password)
        current_token = request.cookies.get(COOKIE_NAME, "")
        db.execute(delete(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.token_hash != hash_session_token(current_token),
        ))

    user.name = payload.name
    user.username = payload.username
    db.commit()
    db.refresh(user)
    return {"user": _user_payload(user)}


@router.patch("/theme")
def update_theme(payload: dict, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    theme = payload.get("theme")
    if theme not in {"dark", "light"}:
        raise HTTPException(status_code=422, detail="Theme must be dark or light")
    user.theme = theme
    db.commit()
    return {"theme": theme}
