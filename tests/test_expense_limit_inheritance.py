from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.models import Base, User, ExpenseLimitPlan, ExpenseLimitComponent
from backend.app.services.expense_limits import get_effective_plan, serialize_effective_plan


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def add_plan(db: Session, user_id: int, year: int, month: int, components: list[tuple[str, str, str]]):
    plan = ExpenseLimitPlan(user_id=user_id, month_key=date(year, month, 1))
    plan.components = [
        ExpenseLimitComponent(description=name, component_type=kind, amount=Decimal(amount))
        for name, kind, amount in components
    ]
    db.add(plan)
    db.flush()
    return plan


def test_months_before_first_plan_have_zero_limit():
    engine = make_db()
    with Session(engine) as db:
        user = User(name="Tester", username="tester", password_hash="test")
        db.add(user)
        db.flush()
        result = serialize_effective_plan(get_effective_plan(db, user.id, date(2026, 2, 1)), date(2026, 2, 1))
        assert result["total_limit"] == 0
        assert result["source_month"] is None
        assert result["components"] == []
    engine.dispose()


def test_month_inherits_latest_plan_until_next_plan():
    engine = make_db()
    with Session(engine) as db:
        user = User(name="Tester", username="tester", password_hash="test")
        db.add(user)
        db.flush()
        add_plan(db, user.id, 2026, 3, [("Housing", "fixed", "3000000"), ("Dining", "additional", "1000000")])
        add_plan(db, user.id, 2026, 6, [("Housing", "fixed", "3500000")])

        april = serialize_effective_plan(get_effective_plan(db, user.id, date(2026, 4, 1)), date(2026, 4, 1))
        may = serialize_effective_plan(get_effective_plan(db, user.id, date(2026, 5, 1)), date(2026, 5, 1))
        june = serialize_effective_plan(get_effective_plan(db, user.id, date(2026, 6, 1)), date(2026, 6, 1))

        assert april["source_month"] == "2026-03"
        assert april["is_inherited"] is True
        assert april["total_limit"] == 4000000
        assert may["total_limit"] == 4000000
        assert june["source_month"] == "2026-06"
        assert june["total_limit"] == 3500000
    engine.dispose()
