from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.core.database import get_db
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.models import Base, AdminAccount


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with Session(engine) as db:
        db.add(AdminAccount(username="root_admin", password_hash=hash_password("adminpass6")))
        db.commit()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()


def get_csrf(client: TestClient, endpoint: str) -> str:
    response = client.get(endpoint)
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_user_registration_and_username_login(client: TestClient):
    token = get_csrf(client, "/api/auth/csrf")
    response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "username": "Test_User", "password": "secret6"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 201
    assert response.json()["user"]["username"] == "test_user"

    assert client.get("/api/auth/me").status_code == 200

    # Logging in with the username succeeds; an email address is not accepted as identity.
    client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies.get("moki_csrf", "")})
    token = get_csrf(client, "/api/auth/csrf")
    login = client.post(
        "/api/auth/login",
        json={"username": "TEST_USER", "password": "secret6"},
        headers={"X-CSRF-Token": token},
    )
    assert login.status_code == 200
    assert login.json()["user"]["username"] == "test_user"


def test_registration_rejects_password_shorter_than_six(client: TestClient):
    token = get_csrf(client, "/api/auth/csrf")
    response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "username": "tester", "password": "12345"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 422


def test_admin_portal_and_user_csrf_are_independent(client: TestClient):
    user_token = get_csrf(client, "/api/auth/csrf")
    user_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "username": "tester", "password": "secret6"},
        headers={"X-CSRF-Token": user_token},
    )
    assert user_response.status_code == 201

    admin_token = get_csrf(client, "/api/admin/csrf")
    admin_response = client.post(
        "/api/admin/login",
        json={"username": "ROOT_ADMIN", "password": "adminpass6"},
        headers={"X-CSRF-Token": admin_token},
    )
    assert admin_response.status_code == 200
    assert client.get("/api/admin/me").json()["admin"]["username"] == "root_admin"
    assert client.get("/api/admin/dashboard").json()["registered_users"] == 1

    # Admin CSRF setup must not invalidate the logged-in user's CSRF token.
    user_csrf_cookie = client.cookies.get("moki_csrf", "")
    response = client.patch(
        "/api/auth/theme",
        json={"theme": "light"},
        headers={"X-CSRF-Token": user_csrf_cookie},
    )
    assert response.status_code == 200
    assert response.json()["theme"] == "light"


def test_admin_can_manage_users_and_create_another_admin(client: TestClient):
    user_csrf = get_csrf(client, "/api/auth/csrf")
    registered = client.post(
        "/api/auth/register",
        json={"name": "Managed User", "username": "managed_user", "password": "firstpass"},
        headers={"X-CSRF-Token": user_csrf},
    )
    assert registered.status_code == 201
    user_id = registered.json()["user"]["id"]

    admin_csrf = get_csrf(client, "/api/admin/csrf")
    login = client.post(
        "/api/admin/login",
        json={"username": "root_admin", "password": "adminpass6"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert login.status_code == 200
    admin_csrf = client.cookies.get("moki_admin_csrf", "")

    created_admin = client.post(
        "/api/admin/administrators",
        json={"username": "second_admin", "password": "second6", "confirm_password": "second6"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert created_admin.status_code == 201
    assert len(client.get("/api/admin/administrators").json()["items"]) == 2

    deactivated = client.post(
        f"/api/admin/users/{user_id}/status",
        json={"action": "deactivate"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert deactivated.status_code == 200
    assert client.get("/api/auth/me").status_code == 401

    reactivated = client.post(
        f"/api/admin/users/{user_id}/status",
        json={"action": "reactivate"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert reactivated.status_code == 200

    reset = client.post(
        f"/api/admin/users/{user_id}/password",
        json={"new_password": "changed6"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert reset.status_code == 200

    new_user_csrf = get_csrf(client, "/api/auth/csrf")
    logged_in = client.post(
        "/api/auth/login",
        json={"username": "managed_user", "password": "changed6"},
        headers={"X-CSRF-Token": new_user_csrf},
    )
    assert logged_in.status_code == 200

    deleted = client.post(
        f"/api/admin/users/{user_id}/delete",
        json={},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert deleted.status_code == 200
    assert client.get("/api/admin/users").json()["items"] == []


def test_dashboard_returns_selected_month_and_cumulative_capped_totals(client: TestClient):
    csrf = get_csrf(client, "/api/auth/csrf")
    registered = client.post(
        "/api/auth/register",
        json={"name": "Finance User", "username": "finance_user", "password": "secret6"},
        headers={"X-CSRF-Token": csrf},
    )
    assert registered.status_code == 201
    csrf = client.cookies.get("moki_csrf", "")

    for month, amount, description in [
        ("2025-01", 1000, "Past salary"),
        ("2030-01", 9000, "Future salary"),
    ]:
        response = client.post(
            "/api/incomes/bulk",
            json={"month": month, "items": [{"description": description, "type": "fixed", "amount": amount}]},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 201

    for month, amount, description in [
        ("2025-01", 400, "Past groceries"),
        ("2030-01", 700, "Future groceries"),
    ]:
        response = client.post(
            "/api/expenses/bulk",
            json={"month": month, "items": [{"description": description, "type": "additional", "amount": amount}]},
            headers={"X-CSRF-Token": csrf},
        )
        assert response.status_code == 201

    dashboard = client.get("/api/dashboard?month=2030-01").json()
    assert dashboard["metrics"]["total_income"] == 9000
    assert dashboard["metrics"]["total_expenses"] == 700
    # Cumulative cards are capped at the current month, even if a future month is selected.
    assert dashboard["all_time_income"] == 1000
    assert dashboard["all_time_expenses"] == 400


def test_financial_mutations_require_session_csrf(client: TestClient):
    token = get_csrf(client, "/api/auth/csrf")
    registered = client.post(
        "/api/auth/register",
        json={"name": "Protected User", "username": "protected_user", "password": "secret6"},
        headers={"X-CSRF-Token": token},
    )
    assert registered.status_code == 201

    payload = {"month": "2026-01", "items": [{"description": "Salary", "type": "fixed", "amount": 1000}]}
    assert client.post("/api/incomes/bulk", json=payload).status_code == 403
    assert client.put("/api/expense-limits/2026-01", json={"components": []}).status_code == 403


def test_user_can_update_profile_and_change_password_without_losing_current_session(client: TestClient):
    token = get_csrf(client, "/api/auth/csrf")
    registered = client.post(
        "/api/auth/register",
        json={"name": "Original Name", "username": "original_user", "password": "oldpass6"},
        headers={"X-CSRF-Token": token},
    )
    assert registered.status_code == 201

    token = client.cookies.get("moki_csrf", "")
    invalid = client.patch(
        "/api/auth/profile",
        json={"name": "Updated Name", "username": "updated_user", "current_password": "wrongpass", "new_password": "newpass6"},
        headers={"X-CSRF-Token": token},
    )
    assert invalid.status_code == 400

    updated = client.patch(
        "/api/auth/profile",
        json={"name": "Updated Name", "username": "updated_user", "current_password": "oldpass6", "new_password": "newpass6"},
        headers={"X-CSRF-Token": token},
    )
    assert updated.status_code == 200
    assert updated.json()["user"]["name"] == "Updated Name"
    assert updated.json()["user"]["username"] == "updated_user"
    assert client.get("/api/auth/me").status_code == 200

    client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies.get("moki_csrf", "")})
    token = get_csrf(client, "/api/auth/csrf")
    assert client.post("/api/auth/login", json={"username": "updated_user", "password": "oldpass6"}, headers={"X-CSRF-Token": token}).status_code == 401
    token = get_csrf(client, "/api/auth/csrf")
    assert client.post("/api/auth/login", json={"username": "updated_user", "password": "newpass6"}, headers={"X-CSRF-Token": token}).status_code == 200


def test_admin_can_update_own_profile_and_view_user_transaction_components(client: TestClient):
    user_csrf = get_csrf(client, "/api/auth/csrf")
    registered = client.post(
        "/api/auth/register",
        json={"name": "Finance Owner", "username": "finance_owner", "password": "secret6"},
        headers={"X-CSRF-Token": user_csrf},
    )
    assert registered.status_code == 201
    user_id = registered.json()["user"]["id"]
    user_csrf = client.cookies.get("moki_csrf", "")
    client.post("/api/incomes/bulk", json={"month": "2026-01", "items": [
        {"description": "Salary", "type": "fixed", "amount": 5000000},
        {"description": "Freelance", "type": "additional", "amount": 750000},
    ]}, headers={"X-CSRF-Token": user_csrf})
    client.post("/api/expenses/bulk", json={"month": "2026-01", "items": [
        {"description": "Rent", "type": "fixed", "amount": 1500000},
        {"description": "Groceries", "type": "additional", "amount": 600000},
    ]}, headers={"X-CSRF-Token": user_csrf})

    admin_csrf = get_csrf(client, "/api/admin/csrf")
    login = client.post("/api/admin/login", json={"username": "root_admin", "password": "adminpass6"}, headers={"X-CSRF-Token": admin_csrf})
    assert login.status_code == 200
    admin_csrf = client.cookies.get("moki_admin_csrf", "")

    detail = client.get(f"/api/admin/users/{user_id}").json()
    assert [(row["description"], row["type"], row["amount"]) for row in detail["income_items"]] == [
        ("Freelance", "additional", 750000.0), ("Salary", "fixed", 5000000.0)
    ]
    assert [(row["description"], row["type"], row["amount"]) for row in detail["expense_items"]] == [
        ("Groceries", "additional", 600000.0), ("Rent", "fixed", 1500000.0)
    ]

    changed = client.patch(
        "/api/admin/profile",
        json={"username": "new_root", "current_password": "adminpass6", "new_password": "adminnew6"},
        headers={"X-CSRF-Token": admin_csrf},
    )
    assert changed.status_code == 200
    assert changed.json()["admin"]["username"] == "new_root"
    assert client.get("/api/admin/me").json()["admin"]["username"] == "new_root"
