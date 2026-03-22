"""Baseline: create schema from ORM metadata (tables, indexes, FKs).

Revision ID: 0001_baseline
Revises:
Create Date: 2026-03-19

"""

from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from src.database.core import Base

    import src.routers.v1.orders.models  # noqa: F401

    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    from src.database.core import Base

    import src.routers.v1.orders.models  # noqa: F401

    Base.metadata.drop_all(bind=bind)
