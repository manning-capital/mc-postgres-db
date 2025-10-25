"""remove_name_and_description_from_provider_asset_group

Revision ID: be643474d39f
Revises: bca303faca0a
Create Date: 2025-10-24 21:47:35.637607

"""

from typing import Union, Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "be643474d39f"
down_revision: Union[str, Sequence[str], None] = "bca303faca0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the name and description columns from provider_asset_group table
    op.drop_column("provider_asset_group", "description")
    op.drop_column("provider_asset_group", "name")


def downgrade() -> None:
    """Downgrade schema."""
    # Add back the name and description columns to provider_asset_group table
    op.add_column(
        "provider_asset_group",
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="The name of the asset group",
        ),
    )
    op.add_column(
        "provider_asset_group",
        sa.Column(
            "description",
            sa.String(length=1000),
            nullable=True,
            comment="The description of the asset group",
        ),
    )
