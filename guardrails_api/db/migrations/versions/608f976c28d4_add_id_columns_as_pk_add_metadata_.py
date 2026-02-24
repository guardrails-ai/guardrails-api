"""Add id columns as pk; add metadata columns; rename railspec to guard

Revision ID: 608f976c28d4
Revises:
Create Date: 2026-02-23 15:41:34.508196

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from guardrails_api.db.extras.audit import (
    AUDIT_FUNCTION_REV_608f976c28d4,
    AUDIT_TRIGGER_REV_608f976c28d4,
    AUDIT_FUNCTION_REV_NONE,
    AUDIT_TRIGGER_REV_NONE,
)

# revision identifiers, used by Alembic.
revision: str = "608f976c28d4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.Inspector.from_engine(bind.engine)

    """Upgrade schema."""
    ## Guards Table
    guard_columns = inspector.get_columns("guards")
    guard_column_names = [col["name"] for col in guard_columns]

    op.add_column(
        "guards",
        sa.Column(
            "id",
            sa.String(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        if_not_exists=True,
    )
    if "railspec" in guard_column_names:
        op.alter_column(
            "guards",
            "railspec",
            new_column_name="guard",
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            existing_nullable=False,
        )
    op.add_column(
        "guards",
        sa.Column(
            "created_by", sa.String(), nullable=True, server_default="guardrails-api"
        ),
        if_not_exists=True,
    )
    op.add_column(
        "guards",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        if_not_exists=True,
    )
    op.add_column(
        "guards",
        sa.Column(
            "updated_by", sa.String(), nullable=True, server_default="guardrails-api"
        ),
        if_not_exists=True,
    )
    op.add_column(
        "guards",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        if_not_exists=True,
    )
    op.create_unique_constraint("guards_name_unique", "guards", ["name"])
    op.drop_column("guards", "description", if_exists=True)
    op.drop_column("guards", "num_reasks", if_exists=True)
    op.drop_constraint("guards_pkey", "guards", type_="primary", if_exists=True)
    op.create_primary_key("pk_guards_id", "guards", ["id"])

    ## Guards Audit Table
    audit_columns = inspector.get_columns("guards_audit")
    audit_column_names = [col["name"] for col in audit_columns]
    op.add_column(
        "guards_audit",
        sa.Column("guard_id", sa.String(), nullable=True),
        if_not_exists=True,
    )

    if "railspec" in audit_column_names:
        op.alter_column(
            "guards_audit",
            "railspec",
            new_column_name="guard",
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            existing_nullable=False,
            if_exists=True,
        )
    op.add_column(
        "guards_audit",
        sa.Column("created_by", sa.String(), nullable=True),
        if_not_exists=True,
    )
    op.add_column(
        "guards_audit",
        sa.Column("created_at", sa.DateTime(), nullable=True),
        if_not_exists=True,
    )
    op.add_column(
        "guards_audit",
        sa.Column("updated_by", sa.String(), nullable=True),
        if_not_exists=True,
    )
    op.add_column(
        "guards_audit",
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        if_not_exists=True,
    )
    op.create_index(
        op.f("ix_guards_audit_guard_id"),
        "guards_audit",
        ["guard_id"],
        unique=False,
        if_not_exists=True,
    )
    op.drop_column("guards_audit", "description", if_exists=True)
    op.drop_column("guards_audit", "num_reasks", if_exists=True)

    ## Audit Function and Trigger
    op.execute(AUDIT_FUNCTION_REV_608f976c28d4)
    op.execute(AUDIT_TRIGGER_REV_608f976c28d4)


def downgrade() -> None:
    """Downgrade schema."""
    ## Audit Function and Trigger
    op.execute(AUDIT_FUNCTION_REV_NONE)
    op.execute(AUDIT_TRIGGER_REV_NONE)

    ## Guards Audit Table
    op.add_column(
        "guards_audit",
        sa.Column("num_reasks", sa.INTEGER(), autoincrement=False, nullable=True),
        if_not_exists=True,
    )
    op.alter_column(
        "guards_audit",
        "guard",
        new_column_name="railspec",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        if_exists=True,
    )
    op.add_column(
        "guards_audit",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        if_not_exists=True,
    )
    op.drop_index(
        op.f("ix_guards_audit_guard_id"), table_name="guards_audit", if_exists=True
    )
    op.drop_column("guards_audit", "updated_at", if_exists=True)
    op.drop_column("guards_audit", "updated_by", if_exists=True)
    op.drop_column("guards_audit", "created_at", if_exists=True)
    op.drop_column("guards_audit", "created_by", if_exists=True)
    op.drop_column("guards_audit", "guard_id", if_exists=True)

    ## Guards Table
    op.add_column(
        "guards",
        sa.Column("num_reasks", sa.INTEGER(), autoincrement=False, nullable=True),
        if_not_exists=True,
    )
    op.alter_column(
        "guards",
        "guard",
        new_column_name="railspec",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        if_exists=True,
    )
    op.add_column(
        "guards",
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        if_not_exists=True,
    )
    op.drop_constraint("guards_name_unique", "guards", type_="unique", if_exists=True)
    op.drop_column("guards", "updated_at", if_exists=True)
    op.drop_column("guards", "updated_by", if_exists=True)
    op.drop_column("guards", "created_at", if_exists=True)
    op.drop_column("guards", "created_by", if_exists=True)
    op.drop_column("guards", "id", if_exists=True)
