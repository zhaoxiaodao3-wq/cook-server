"""Align database schema with frontend API spec

Revision ID: 002
Revises: 001
Create Date: 2026-06-04

Changes:
- users: add bio column
- categories: add key column
- dishes: add cuisine, tags columns
- ingredients: change amount from NUMERIC to VARCHAR
- NEW: favorites table
- NEW: drafts table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users: add bio
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))

    # categories: add key
    op.add_column("categories", sa.Column("key", sa.String(32), nullable=True))
    op.create_unique_constraint("uq_categories_key", "categories", ["key"])

    # dishes: add cuisine, tags
    op.add_column("dishes", sa.Column("cuisine", sa.String(32), nullable=True))
    op.add_column("dishes", sa.Column("tags", postgresql.JSONB(), nullable=True))

    # ingredients: change amount column type
    op.alter_column("ingredients", "amount",
                     existing_type=sa.NUMERIC(8, 2),
                     type_=sa.String(32),
                     existing_nullable=False,
                     postgresql_using="amount::varchar")

    # favorites table
    op.create_table(
        "favorites",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("dish_id", sa.String(36), sa.ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "dish_id"),
    )

    # drafts table
    op.create_table(
        "drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(128), nullable=True),
        sa.Column("step", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cover_image", sa.String(512), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("difficulty", sa.String(8), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("ingredients", postgresql.JSONB(), nullable=True),
        sa.Column("steps", postgresql.JSONB(), nullable=True),
        sa.Column("category", sa.String(32), nullable=True),
        sa.Column("cuisine", sa.String(32), nullable=True),
        sa.Column("tags", postgresql.JSONB(), nullable=True),
        sa.Column("crowd", sa.String(128), nullable=True),
        sa.Column("tips", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Seed default categories with keys
    op.execute("""
        INSERT INTO categories (name, key, icon, sort_order) VALUES
        ('早餐', 'breakfast', 'sunrise', 1),
        ('午餐', 'lunch', 'sun', 2),
        ('晚餐', 'dinner', 'moon', 3),
        ('甜品', 'dessert', 'cake', 4)
        ON CONFLICT (name) DO UPDATE SET key = EXCLUDED.key
    """)


def downgrade() -> None:
    op.drop_table("drafts")
    op.drop_table("favorites")
    op.drop_column("dishes", "tags")
    op.drop_column("dishes", "cuisine")
    op.drop_constraint("uq_categories_key", "categories", type_="unique")
    op.drop_column("categories", "key")
    op.alter_column("ingredients", "amount",
                     existing_type=sa.String(32),
                     type_=sa.NUMERIC(8, 2),
                     existing_nullable=False,
                     postgresql_using="amount::numeric")
    op.drop_column("users", "bio")
