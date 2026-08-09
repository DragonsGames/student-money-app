"""Add interface preferences

Revision ID: e4b7a1c9d203
Revises: d9a6e3f71b42
Create Date: 2026-08-09

"""
from alembic import op
import sqlalchemy as sa


revision = "e4b7a1c9d203"
down_revision = "d9a6e3f71b42"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "appearance",
                sa.String(length=20),
                server_default="system",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "language",
                sa.String(length=5),
                server_default="en",
                nullable=False,
            )
        )


def downgrade():
    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.drop_column("language")
        batch_op.drop_column("appearance")
