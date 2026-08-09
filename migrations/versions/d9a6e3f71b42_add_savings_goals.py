"""Add savings goals

Revision ID: d9a6e3f71b42
Revises: c8f4a12d9e70
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d9a6e3f71b42"
down_revision = "c8f4a12d9e70"
branch_labels = None
depends_on = None


# AI assistance: OpenAI Codex assisted with drafting this SavingsGoal
# migration; reviewed by the project author. It has not been applied.
def upgrade():
    op.create_table(
        "savings_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "target_amount",
            sa.Numeric(precision=12, scale=3),
            nullable=False
        ),
        sa.Column(
            "saved_amount",
            sa.Numeric(precision=12, scale=3),
            server_default="0.000",
            nullable=False
        ),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False
        ),
        sa.CheckConstraint(
            "saved_amount >= 0",
            name="ck_savings_goals_saved_nonnegative"
        ),
        sa.CheckConstraint(
            "target_amount > 0",
            name="ck_savings_goals_target_positive"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id")
    )


def downgrade():
    op.drop_table("savings_goals")
