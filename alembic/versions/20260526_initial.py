"""Initial migration

Revision ID: 20260526_initial
Revises:
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260526_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建所有表（基于当前模型）
    # Alembic 会自动检测，这里留空让 autogenerate 生成
    pass


def downgrade() -> None:
    pass
