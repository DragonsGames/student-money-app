"""Add transactions

Revision ID: b7e16a4c2d91
Revises: 39eb33845a25
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7e16a4c2d91"
down_revision = "39eb33845a25"
branch_labels = None
depends_on = None


# AI assistance: OpenAI Codex assisted with drafting this migration; reviewed
# and adapted by the project author. It has not been applied to the database.
def upgrade():
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=12, scale=3),
            nullable=False
        ),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_transactions_amount_positive"
        ),
        sa.CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_type"
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade():
    op.drop_table("transactions")
