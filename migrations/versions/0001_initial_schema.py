"""Create Moki tables.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-21
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("theme", sa.String(length=10), nullable=False, server_default="dark"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    for table in ("incomes", "expenses"):
        field = "income_type" if table == "incomes" else "expense_type"
        op.create_table(
            table,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("month_key", sa.Date(), nullable=False),
            sa.Column("description", sa.String(length=160), nullable=False),
            sa.Column(field, sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Numeric(14, 2), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(f"ix_{table}_user_month", table, ["user_id", "month_key"])
    op.create_table(
        "expense_limit_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month_key", sa.Date(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "month_key", name="uq_expense_limit_user_month"),
    )
    op.create_index("ix_expense_limit_plans_user_id", "expense_limit_plans", ["user_id"])
    op.create_table(
        "expense_limit_components",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("expense_limit_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(length=160), nullable=False),
        sa.Column("component_type", sa.String(length=20), nullable=False, server_default="fixed"),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
    )
    op.create_index("ix_expense_limit_components_plan_id", "expense_limit_components", ["plan_id"])
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


def downgrade():
    op.drop_table("expense_standards")
    op.drop_index("ix_expense_limit_components_plan_id", table_name="expense_limit_components")
    op.drop_table("expense_limit_components")
    op.drop_index("ix_expense_limit_plans_user_id", table_name="expense_limit_plans")
    op.drop_table("expense_limit_plans")
    for table in ("expenses", "incomes"):
        op.drop_index(f"ix_{table}_user_month", table_name=table)
        op.drop_table(table)
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
