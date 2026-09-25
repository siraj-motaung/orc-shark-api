"""add user role

Revision ID: 24b6a1828dfd
Revises: 6dbee3426e7b
Create Date: 2026-09-16 03:15:00.604341

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '24b6a1828dfd'
down_revision: str | Sequence[str] | None = '6dbee3426e7b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    user_role = sa.Enum(
        "CUSTOMER",
        "ADMIN",
        name="userrole",
    )

    user_role.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role,
            nullable=False,
            server_default="CUSTOMER",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "role")

    user_role = sa.Enum(
        "CUSTOMER",
        "ADMIN",
        name="userrole",
    )

    user_role.drop(op.get_bind(), checkfirst=True)
