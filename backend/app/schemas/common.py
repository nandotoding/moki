from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
import re
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def parse_month(value: str | date | None) -> date:
    if value is None:
        today = date.today()
        return date(today.year, today.month, 1)
    if isinstance(value, date):
        return date(value.year, value.month, 1)
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise HTTPException(status_code=422, detail="Month must use YYYY-MM format")
    year, month = map(int, value.split("-"))
    if month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="Month must be between 01 and 12")
    return date(year, month, 1)


def decimal_value(value: Decimal | int | float | str) -> Decimal:
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid number")
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    if amount > Decimal("999999999999.99"):
        raise ValueError("Amount is too large")
    return amount


class TransactionRow(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    type: str = Field(pattern="^(fixed|additional)$")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Description is required")
        return cleaned


class BulkTransactions(BaseModel):
    month: str
    items: list[TransactionRow] = Field(min_length=1, max_length=100)


class TransactionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=160)
    type: str | None = Field(default=None, pattern="^(fixed|additional)$")
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Description is required")
        return cleaned


class LimitComponentInput(BaseModel):
    description: str = Field(min_length=1, max_length=160)
    type: str = Field(pattern="^(fixed|additional)$")
    amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Description is required")
        return cleaned


class ExpenseLimitUpdate(BaseModel):
    components: list[LimitComponentInput] = Field(max_length=100)
