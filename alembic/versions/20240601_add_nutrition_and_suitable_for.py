"""add nutrition and suitable_for columns to dishes

Revision ID: 001
Revises:
Create Date: 2024-06-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dishes", sa.Column("nutrition", sa.Text(), nullable=True))
    op.add_column("dishes", sa.Column("suitable_for", sa.String(128), nullable=True))


def downgrade() -> None:
    op.drop_column("dishes", "suitable_for")
    op.drop_column("dishes", "nutrition")
