"""Add budgets

Revision ID: c8f4a12d9e70
Revises: b7e16a4c2d91
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c8f4a12d9e70"
down_revision = "b7e16a4c2d91"
branch_labels = None
depends_on = None


# AI assistance: OpenAI Codex assisted with drafting this Budget migration;
# reviewed and adapted by the project author. It has not been applied.
def upgrade():
    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=12, scale=3),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False
        ),
        sa.CheckConstraint(
            "amount > 0",
            name="ck_budgets_amount_positive"
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "category_id",
            name="uq_budgets_user_category"
        )
    )


def downgrade():
    op.drop_table("budgets")
