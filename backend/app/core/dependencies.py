from __future__ import annotations

import hmac
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import COOKIE_NAME, ADMIN_COOKIE_NAME, CSRF_COOKIE_NAME, ADMIN_CSRF_COOKIE_NAME
from backend.app.core.database import get_db
from backend.app.core.security import hash_session_token
from backend.app.models.entities import User, UserSession, AdminAccount, AdminSession


def _csrf_ok(request: Request, expected_hash: str, cookie_name: str = CSRF_COOKIE_NAME) -> bool:
    cookie_token = request.cookies.get(cookie_name, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        return False
    return hmac.compare_digest(hash_session_token(cookie_token), expected_hash)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    statement = select(UserSession).where(
        UserSession.token_hash == hash_session_token(token),
        UserSession.expires_at > datetime.now(timezone.utc),
    )
    session = db.scalar(statement)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please sign in again.")
    user = db.get(User, session.user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account unavailable")
    return user


def verify_user_csrf(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    token = request.cookies.get(COOKIE_NAME, "")
    session = db.scalar(select(UserSession).where(
        UserSession.user_id == user.id,
        UserSession.token_hash == hash_session_token(token),
        UserSession.expires_at > datetime.now(timezone.utc),
    ))
    if not session or not _csrf_ok(request, session.csrf_token_hash):
        raise HTTPException(status_code=403, detail="CSRF validation failed")


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> AdminAccount:
    token = request.cookies.get(ADMIN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Administrator authentication required")
    session = db.scalar(select(AdminSession).where(
        AdminSession.token_hash == hash_session_token(token),
        AdminSession.expires_at > datetime.now(timezone.utc),
    ))
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Administrator session expired")
    admin = db.get(AdminAccount, session.admin_id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Administrator account unavailable")
    return admin


def verify_admin_csrf(
    request: Request,
    admin: AdminAccount = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> None:
    token = request.cookies.get(ADMIN_COOKIE_NAME, "")
    session = db.scalar(select(AdminSession).where(
        AdminSession.admin_id == admin.id,
        AdminSession.token_hash == hash_session_token(token),
        AdminSession.expires_at > datetime.now(timezone.utc),
    ))
    if not session or not _csrf_ok(request, session.csrf_token_hash, ADMIN_CSRF_COOKIE_NAME):
        raise HTTPException(status_code=403, detail="CSRF validation failed")
