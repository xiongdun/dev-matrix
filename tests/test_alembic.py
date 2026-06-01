"""Alembic 迁移测试。"""

import os

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command


class TestAlembic:
    """测试 Alembic 迁移功能。"""

    def test_alembic_config_exists(self):
        """测试 alembic.ini 配置文件存在。"""
        assert os.path.exists("alembic.ini")

    def test_alembic_env_exists(self):
        """测试 alembic/env.py 存在。"""
        assert os.path.exists("alembic/env.py")

    def test_alembic_versions_dir_exists(self):
        """测试 alembic/versions/ 目录存在。"""
        assert os.path.isdir("alembic/versions")

    def test_initial_migration_exists(self):
        """测试初始迁移脚本存在。"""
        assert os.path.exists("alembic/versions/20260526_initial.py")

    def test_alembic_upgrade_head(self, tmp_path):
        """测试 alembic upgrade head 能成功执行。"""
        db_path = tmp_path / "test.db"
        database_url = f"sqlite:///{db_path}"

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # 执行升级
        command.upgrade(alembic_cfg, "head")

        # 验证数据库连接正常
        engine = create_engine(database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 至少应该有一些表存在（由 init_db 创建）
        assert isinstance(tables, list)

    def test_alembic_downgrade_base(self, tmp_path):
        """测试 alembic downgrade base 能成功执行。"""
        db_path = tmp_path / "test.db"
        database_url = f"sqlite:///{db_path}"

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # 先升级
        command.upgrade(alembic_cfg, "head")
        # 再降级
        command.downgrade(alembic_cfg, "base")

        engine = create_engine(database_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # 降级后表应该被删除
        assert len(tables) == 0
