from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, verify_user_csrf
from backend.app.models.entities import User, Income, Expense
from backend.app.schemas.common import BulkTransactions, TransactionUpdate, parse_month

router = APIRouter(prefix="/api", tags=["transactions"])


def _serialize(item, kind: str) -> dict:
    transaction_type = item.income_type if kind == "income" else item.expense_type
    return {
        "id": item.id,
        "description": item.description,
        "type": transaction_type,
        "amount": float(item.amount),
        "month": item.month_key.strftime("%Y-%m"),
        "created_at": item.created_at.isoformat(),
    }


def _model(kind: str):
    if kind == "income":
        return Income, "income_type"
    return Expense, "expense_type"


def _list(kind: str, month: str, user: User, db: Session):
    model, _ = _model(kind)
    month_key = parse_month(month)
    statement = select(model).where(model.user_id == user.id, model.month_key == month_key).order_by(model.created_at.desc(), model.id.desc())
    return [_serialize(item, kind) for item in db.scalars(statement).all()]


def _bulk(kind: str, payload: BulkTransactions, user: User, db: Session):
    model, type_field = _model(kind)
    month_key = parse_month(payload.month)
    items = [model(user_id=user.id, month_key=month_key, description=row.description, **{type_field: row.type}, amount=row.amount) for row in payload.items]
    db.add_all(items)
    db.commit()
    for item in items:
        db.refresh(item)
    return {"created": len(items), "items": [_serialize(item, kind) for item in items]}


def _update(kind: str, item_id: int, payload: TransactionUpdate, user: User, db: Session):
    model, type_field = _model(kind)
    item = db.scalar(select(model).where(model.id == item_id, model.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail=f"{kind.title()} transaction not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(item, type_field if field == "type" else field, value)
    db.commit()
    db.refresh(item)
    return _serialize(item, kind)


def _delete(kind: str, item_id: int, user: User, db: Session):
    model, _ = _model(kind)
    item = db.scalar(select(model).where(model.id == item_id, model.user_id == user.id))
    if not item:
        raise HTTPException(status_code=404, detail=f"{kind.title()} transaction not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get("/incomes")
def list_incomes(month: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"items": _list("income", month, user, db)}


@router.post("/incomes/bulk", status_code=201)
def bulk_incomes(payload: BulkTransactions, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    return _bulk("income", payload, user, db)


@router.patch("/incomes/{item_id}")
def update_income(item_id: int, payload: TransactionUpdate, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    return _update("income", item_id, payload, user, db)


@router.delete("/incomes/{item_id}")
def delete_income(item_id: int, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    return _delete("income", item_id, user, db)


@router.get("/expenses")
def list_expenses(month: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"items": _list("expense", month, user, db)}


@router.post("/expenses/bulk", status_code=201)
def bulk_expenses(payload: BulkTransactions, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    return _bulk("expense", payload, user, db)


@router.patch("/expenses/{item_id}")
def update_expense(item_id: int, payload: TransactionUpdate, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    return _update("expense", item_id, payload, user, db)


@router.delete("/expenses/{item_id}")
def delete_expense(item_id: int, user: User = Depends(get_current_user), _csrf: None = Depends(verify_user_csrf), db: Session = Depends(get_db)):
    return _delete("expense", item_id, user, db)
