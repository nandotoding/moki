"""Add username auth and admin portal; remove legacy expense standards.

Revision ID: 0002_usernames_admin
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa
import re

revision = "0002_usernames_admin"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _username_from_email(email: str | None, user_id: int, used: set[str]) -> str:
    local = (email or "").split("@", 1)[0].lower()
    base = re.sub(r"[^a-z0-9_]", "_", local).strip("_")
    if len(base) < 3:
        base = f"user{user_id}"
    base = base[:40]
    candidate = base
    suffix = 1
    while candidate in used:
        suffix += 1
        candidate = f"{base[:42-len(str(suffix))]}_{suffix}"
    used.add(candidate)
    return candidate


def upgrade():
    op.add_column("users", sa.Column("username", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    bind = op.get_bind()
    users = sa.table("users", sa.column("id", sa.Integer), sa.column("email", sa.String), sa.column("username", sa.String))
    used: set[str] = set()
    for row in bind.execute(sa.select(users.c.id, users.c.email).order_by(users.c.id)):
        username = _username_from_email(row.email, row.id, used)
        bind.execute(users.update().where(users.c.id == row.id).values(username=username))
    op.drop_index("ix_users_email", table_name="users")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("username", existing_type=sa.String(length=50), nullable=False)
        batch_op.drop_column("email")
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # Invalidate legacy sessions because they do not have session-bound CSRF tokens.
    op.add_column("user_sessions", sa.Column("csrf_token_hash", sa.String(length=64), nullable=True))
    op.execute(sa.text("DELETE FROM user_sessions"))
    with op.batch_alter_table("user_sessions") as batch_op:
        batch_op.alter_column("csrf_token_hash", existing_type=sa.String(length=64), nullable=False)

    op.create_table(
        "admin_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username", name="uq_admin_accounts_username"),
    )
    op.create_index("ix_admin_accounts_username", "admin_accounts", ["username"], unique=True)

    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admin_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_admin_sessions_token_hash"),
    )
    op.create_index("ix_admin_sessions_admin_id", "admin_sessions", ["admin_id"])
    op.create_index("ix_admin_sessions_token_hash", "admin_sessions", ["token_hash"], unique=True)

    # Expense Standards was the old name and a separate feature; Expense Limits replace it.
    op.drop_index("ix_expense_standards_user_id", table_name="expense_standards")
    op.drop_table("expense_standards")


def downgrade():
    op.create_table(
        "expense_standards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(length=160), nullable=False),
        sa.Column("expense_type", sa.String(length=20), nullable=False, server_default="fixed"),
        sa.Column("expected_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "description", name="uq_expense_standard_user_description"),
    )
    op.create_index("ix_expense_standards_user_id", "expense_standards", ["user_id"])
    op.drop_index("ix_admin_sessions_token_hash", table_name="admin_sessions")
    op.drop_index("ix_admin_sessions_admin_id", table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_index("ix_admin_accounts_username", table_name="admin_accounts")
    op.drop_table("admin_accounts")
    op.drop_column("user_sessions", "csrf_token_hash")
    op.drop_index("ix_users_username", table_name="users")
    # Recreate a compatibility email column when downgrading to the v1 schema.
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    bind = op.get_bind()
    users = sa.table("users", sa.column("id", sa.Integer), sa.column("username", sa.String), sa.column("email", sa.String))
    for row in bind.execute(sa.select(users.c.id, users.c.username)):
        bind.execute(users.update().where(users.c.id == row.id).values(email=f"{row.username}@legacy.moki.local"))
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(length=255), nullable=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "is_active")
    op.drop_column("users", "username")
