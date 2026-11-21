from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session, selectinload

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, verify_user_csrf
from backend.app.models.entities import User, ExpenseLimitPlan, ExpenseLimitComponent
from backend.app.schemas.common import ExpenseLimitUpdate, parse_month
from backend.app.services.expense_limits import get_effective_plan, serialize_effective_plan

router = APIRouter(prefix="/api/expense-limits", tags=["expense limits"])


@router.get("")
def get_expense_limit(month: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    month_key = parse_month(month)
    plan = get_effective_plan(db, user.id, month_key)
    return serialize_effective_plan(plan, month_key)


@router.get("/history")
def get_expense_limit_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    statement = select(ExpenseLimitPlan).options(selectinload(ExpenseLimitPlan.components)).where(
        ExpenseLimitPlan.user_id == user.id
    ).order_by(ExpenseLimitPlan.month_key.desc())
    result = []
    for plan in db.scalars(statement).all():
        result.append(serialize_effective_plan(plan, plan.month_key))
    return {"items": result}


@router.put("/{month}")
def save_expense_limit(month: str, payload: ExpenseLimitUpdate, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    month_key = parse_month(month)
    plan = db.scalar(select(ExpenseLimitPlan).where(ExpenseLimitPlan.user_id == user.id, ExpenseLimitPlan.month_key == month_key))
    if plan is None:
        plan = ExpenseLimitPlan(user_id=user.id, month_key=month_key)
        db.add(plan)
        db.flush()
    else:
        plan.components.clear()
    plan.updated_at = datetime.now(timezone.utc)
    plan.components.extend([
        ExpenseLimitComponent(description=row.description, component_type=row.type, amount=row.amount)
        for row in payload.components
    ])
    db.commit()
    plan = db.scalar(select(ExpenseLimitPlan).options(selectinload(ExpenseLimitPlan.components)).where(ExpenseLimitPlan.id == plan.id))
    return serialize_effective_plan(plan, month_key)


@router.delete("/{month}")
def delete_expense_limit(month: str, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    month_key = parse_month(month)
    plan = db.scalar(select(ExpenseLimitPlan).where(ExpenseLimitPlan.user_id == user.id, ExpenseLimitPlan.month_key == month_key))
    if not plan:
        raise HTTPException(status_code=404, detail="No explicit expense limit is set for this month")
    db.delete(plan)
    db.commit()
    effective = get_effective_plan(db, user.id, month_key)
    return serialize_effective_plan(effective, month_key)
