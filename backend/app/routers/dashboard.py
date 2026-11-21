from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.entities import User, Income, Expense
from backend.app.schemas.common import parse_month
from backend.app.services.expense_limits import get_effective_plan, serialize_effective_plan

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _sum(items, field: str, value: str) -> Decimal:
    return sum((item.amount for item in items if getattr(item, field) == value), Decimal("0"))


@router.get("")
def dashboard(month: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    month_key = parse_month(month)
    incomes = db.scalars(select(Income).where(Income.user_id == user.id, Income.month_key == month_key)).all()
    expenses = db.scalars(select(Expense).where(Expense.user_id == user.id, Expense.month_key == month_key)).all()
    limit = serialize_effective_plan(get_effective_plan(db, user.id, month_key), month_key)

    # Preserve Cibeo's cumulative cards: include records through the selected
    # month, capped at the current month so future-dated transactions are not
    # counted as historical totals.
    current_month = datetime.now(ZoneInfo("Asia/Jakarta")).date().replace(day=1)
    all_time_cutoff = min(month_key, current_month)
    all_time_income = db.scalar(
        select(func.coalesce(func.sum(Income.amount), 0)).where(
            Income.user_id == user.id,
            Income.month_key <= all_time_cutoff,
        )
    ) or Decimal("0")
    all_time_expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == user.id,
            Expense.month_key <= all_time_cutoff,
        )
    ) or Decimal("0")

    fixed_income = _sum(incomes, "income_type", "fixed")
    additional_income = _sum(incomes, "income_type", "additional")
    fixed_expenses = _sum(expenses, "expense_type", "fixed")
    additional_expenses = _sum(expenses, "expense_type", "additional")
    total_income = fixed_income + additional_income
    total_expenses = fixed_expenses + additional_expenses
    expense_by_description: dict[str, Decimal] = {}
    for expense in expenses:
        expense_by_description[expense.description] = expense_by_description.get(expense.description, Decimal("0")) + expense.amount

    return {
        "month": month_key.strftime("%Y-%m"),
        "all_time_income": float(all_time_income),
        "all_time_expenses": float(all_time_expenses),
        "metrics": {
            "expense_limit": limit["total_limit"],
            "fixed_expense_limit": limit["fixed_limit"],
            "total_income": float(total_income),
            "fixed_income": float(fixed_income),
            "additional_income": float(additional_income),
            "total_expenses": float(total_expenses),
            "fixed_expenses": float(fixed_expenses),
            "additional_expenses": float(additional_expenses),
            "surplus_deficit": float(total_income - total_expenses),
            "fixed_income_balance": float(fixed_income - fixed_expenses),
            "remaining_fixed_income": float(fixed_income - total_expenses),
        },
        "expense_breakdown": [
            {"description": name, "amount": float(amount)}
            for name, amount in sorted(expense_by_description.items(), key=lambda pair: pair[1], reverse=True)
        ],
        "limit": limit,
        "transaction_counts": {"income": len(incomes), "expense": len(expenses)},
    }
