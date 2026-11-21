from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hmac
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session

from backend.app.core.config import ADMIN_COOKIE_NAME, ADMIN_CSRF_COOKIE_NAME, ADMIN_SESSION_HOURS, COOKIE_SECURE
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_admin, verify_admin_csrf
from backend.app.core.security import hash_password, verify_password, new_session_token, hash_session_token
from backend.app.models.entities import AdminAccount, AdminSession, User, UserSession, Income, Expense

router = APIRouter(prefix="/api/admin", tags=["admin portal"])


class AdminLoginInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class CreateAdminInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    confirm_password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,50}", value):
            raise ValueError("Username must be 3–50 characters and use lowercase letters, numbers, or underscores")
        return value


class AdminProfileInput(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str | None = Field(default=None, min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_profile_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]{3,50}", value):
            raise ValueError("Username must be 3–50 characters and use lowercase letters, numbers, or underscores")
        return value


class UserStatusInput(BaseModel):
    action: str = Field(pattern="^(deactivate|reactivate)$")


class ResetPasswordInput(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


def _verify_pre_auth_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(ADMIN_CSRF_COOKIE_NAME, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="CSRF validation failed. Refresh the page and try again.")


def _set_admin_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    max_age = ADMIN_SESSION_HOURS * 60 * 60
    response.set_cookie(key=ADMIN_COOKIE_NAME, value=session_token, max_age=max_age, httponly=True,
                        secure=COOKIE_SECURE, samesite="lax", path="/")
    response.set_cookie(key=ADMIN_CSRF_COOKIE_NAME, value=csrf_token, max_age=max_age, httponly=False,
                        secure=COOKIE_SECURE, samesite="lax", path="/")


def _admin_payload(admin: AdminAccount) -> dict:
    return {"id": admin.id, "username": admin.username, "created_at": admin.created_at.isoformat()}


@router.get("/csrf")
def get_admin_csrf_token(response: Response):
    token = secrets.token_urlsafe(32)
    response.set_cookie(key=ADMIN_CSRF_COOKIE_NAME, value=token, max_age=7200, httponly=False,
                        secure=COOKIE_SECURE, samesite="lax", path="/")
    return {"csrf_token": token}


@router.post("/login")
def login(payload: AdminLoginInput, request: Request, response: Response, db: Session = Depends(get_db)):
    _verify_pre_auth_csrf(request)
    admin = db.scalar(select(AdminAccount).where(AdminAccount.username == payload.username))
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid administrator username or password")
    now = datetime.now(timezone.utc)
    db.execute(delete(AdminSession).where(AdminSession.expires_at < now))
    session_token = new_session_token()
    csrf_token = secrets.token_urlsafe(32)
    db.add(AdminSession(admin_id=admin.id, token_hash=hash_session_token(session_token),
                        csrf_token_hash=hash_session_token(csrf_token),
                        expires_at=now + timedelta(hours=ADMIN_SESSION_HOURS)))
    db.commit()
    _set_admin_cookies(response, session_token, csrf_token)
    return {"admin": _admin_payload(admin)}


@router.get("/me")
def me(admin: AdminAccount = Depends(get_current_admin)):
    return {"admin": _admin_payload(admin)}


@router.patch("/profile")
def update_admin_profile(
    payload: AdminProfileInput,
    request: Request,
    admin: AdminAccount = Depends(get_current_admin),
    _csrf: None = Depends(verify_admin_csrf),
    db: Session = Depends(get_db),
):
    existing = db.scalar(select(AdminAccount).where(
        AdminAccount.username == payload.username,
        AdminAccount.id != admin.id,
    ))
    if existing:
        raise HTTPException(status_code=409, detail="This administrator username is already in use")

    if payload.new_password:
        if not payload.current_password or not verify_password(payload.current_password, admin.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        admin.password_hash = hash_password(payload.new_password)
        current_token = request.cookies.get(ADMIN_COOKIE_NAME, "")
        db.execute(delete(AdminSession).where(
            AdminSession.admin_id == admin.id,
            AdminSession.token_hash != hash_session_token(current_token),
        ))

    admin.username = payload.username
    db.commit()
    db.refresh(admin)
    return {"admin": _admin_payload(admin)}


@router.post("/logout")
def logout(request: Request, response: Response, admin: AdminAccount = Depends(get_current_admin),
           _csrf: None = Depends(verify_admin_csrf), db: Session = Depends(get_db)):
    token = request.cookies.get(ADMIN_COOKIE_NAME)
    if token:
        db.execute(delete(AdminSession).where(AdminSession.token_hash == hash_session_token(token)))
        db.commit()
    response.delete_cookie(ADMIN_COOKIE_NAME, path="/", secure=COOKIE_SECURE, httponly=True, samesite="lax")
    response.delete_cookie(ADMIN_CSRF_COOKIE_NAME, path="/", secure=COOKIE_SECURE, httponly=False, samesite="lax")
    return {"ok": True}


@router.get("/dashboard")
def dashboard(admin: AdminAccount = Depends(get_current_admin), db: Session = Depends(get_db)):
    registered = db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None))) or 0
    active = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(True), User.deleted_at.is_(None))) or 0
    inactive = db.scalar(select(func.count()).select_from(User).where(User.is_active.is_(False), User.deleted_at.is_(None))) or 0
    deleted = db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_not(None))) or 0
    admins = db.scalar(select(func.count()).select_from(AdminAccount)) or 0
    return {"registered_users": registered, "active_users": active, "inactive_users": inactive,
            "deleted_users": deleted, "administrators": admins}


@router.get("/users")
def list_users(admin: AdminAccount = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.scalars(select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())).all()
    return {"items": [{"id": user.id, "name": user.name, "username": user.username,
                        "is_active": user.is_active, "created_at": user.created_at.isoformat()} for user in users]}


@router.get("/users/{user_id}")
def user_detail(user_id: int, admin: AdminAccount = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    income_count, income_total = db.execute(select(func.count(Income.id), func.coalesce(func.sum(Income.amount), 0)).where(Income.user_id == user.id)).one()
    expense_count, expense_total = db.execute(select(func.count(Expense.id), func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == user.id)).one()
    income_items = db.scalars(
        select(Income).where(Income.user_id == user.id)
        .order_by(Income.month_key.desc(), Income.created_at.desc(), Income.id.desc())
    ).all()
    expense_items = db.scalars(
        select(Expense).where(Expense.user_id == user.id)
        .order_by(Expense.month_key.desc(), Expense.created_at.desc(), Expense.id.desc())
    ).all()

    def transaction_payload(item, transaction_type: str) -> dict:
        return {
            "id": item.id,
            "month": item.month_key.strftime("%Y-%m"),
            "description": item.description,
            "type": getattr(item, f"{transaction_type}_type"),
            "amount": float(item.amount),
            "created_at": item.created_at.isoformat(),
        }

    return {
        "id": user.id, "name": user.name, "username": user.username, "is_active": user.is_active,
        "created_at": user.created_at.isoformat(), "income_count": income_count,
        "income_total": float(income_total), "expense_count": expense_count,
        "expense_total": float(expense_total),
        "income_items": [transaction_payload(item, "income") for item in income_items],
        "expense_items": [transaction_payload(item, "expense") for item in expense_items],
    }


@router.post("/users/{user_id}/status")
def update_user_status(user_id: int, payload: UserStatusInput,
                       admin: AdminAccount = Depends(get_current_admin),
                       _csrf: None = Depends(verify_admin_csrf), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.action == "deactivate":
        user.is_active = False
        db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    else:
        user.is_active = True
    db.commit()
    return {"ok": True, "is_active": user.is_active}


@router.post("/users/{user_id}/password")
def reset_user_password(user_id: int, payload: ResetPasswordInput,
                        admin: AdminAccount = Depends(get_current_admin),
                        _csrf: None = Depends(verify_admin_csrf), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/delete")
def soft_delete_user(user_id: int, admin: AdminAccount = Depends(get_current_admin),
                     _csrf: None = Depends(verify_admin_csrf), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    db.commit()
    return {"ok": True}


@router.get("/administrators")
def list_administrators(admin: AdminAccount = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = db.scalars(select(AdminAccount).order_by(AdminAccount.created_at.desc())).all()
    return {"items": [_admin_payload(item) for item in items]}


@router.post("/administrators", status_code=201)
def create_administrator(payload: CreateAdminInput,
                         admin: AdminAccount = Depends(get_current_admin),
                         _csrf: None = Depends(verify_admin_csrf), db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")
    if db.scalar(select(AdminAccount.id).where(AdminAccount.username == payload.username)):
        raise HTTPException(status_code=409, detail="This administrator username is already registered")
    new_admin = AdminAccount(username=payload.username, password_hash=hash_password(payload.password))
    db.add(new_admin)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_admin)
    return _admin_payload(new_admin)
