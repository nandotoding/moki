from __future__ import annotations

from datetime import date
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models.entities import ExpenseLimitPlan


def get_effective_plan(db: Session, user_id: int, month_key: date) -> ExpenseLimitPlan | None:
    statement = (
        select(ExpenseLimitPlan)
        .options(selectinload(ExpenseLimitPlan.components))
        .where(ExpenseLimitPlan.user_id == user_id, ExpenseLimitPlan.month_key <= month_key)
        .order_by(ExpenseLimitPlan.month_key.desc())
        .limit(1)
    )
    return db.scalar(statement)


def serialize_effective_plan(plan: ExpenseLimitPlan | None, requested_month: date) -> dict:
    components = [] if plan is None else [
        {
            "id": item.id,
            "description": item.description,
            "type": item.component_type,
            "amount": float(item.amount),
        }
        for item in plan.components
    ]
    total = sum((Decimal(str(item["amount"])) for item in components), Decimal("0"))
    fixed = sum((Decimal(str(item["amount"])) for item in components if item["type"] == "fixed"), Decimal("0"))
    additional = total - fixed
    return {
        "month": requested_month.strftime("%Y-%m"),
        "source_month": plan.month_key.strftime("%Y-%m") if plan else None,
        "is_inherited": bool(plan and plan.month_key != requested_month),
        "has_explicit_plan": bool(plan and plan.month_key == requested_month),
        "components": components,
        "total_limit": float(total),
        "fixed_limit": float(fixed),
        "additional_limit": float(additional),
    }
