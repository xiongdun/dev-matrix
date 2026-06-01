"""密钥管理模块测试。"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.secrets import (
    DEFAULT_SECRET_KEY_NAME,
    generate_secret_key,
    get_or_create_secret,
    get_secret,
    rotate_secret,
)
from app.state.models import Base, SystemSecretModel


@pytest.fixture
def db_session():
    """创建内存数据库会话。"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


class TestGenerateSecretKey:
    def test_default_length(self):
        key = generate_secret_key()
        assert len(key) == 64

    def test_custom_length(self):
        key = generate_secret_key(32)
        assert len(key) == 32

    def test_unique_keys(self):
        key1 = generate_secret_key()
        key2 = generate_secret_key()
        assert key1 != key2

    def test_hex_format(self):
        key = generate_secret_key()
        int(key, 16)  # 应该能成功解析为十六进制


class TestGetOrCreateSecret:
    def test_creates_new_secret(self, db_session):
        key = get_or_create_secret(db_session)
        assert len(key) == 64
        # 验证数据库中有记录
        record = (
            db_session.query(SystemSecretModel)
            .filter(SystemSecretModel.key_name == DEFAULT_SECRET_KEY_NAME)
            .first()
        )
        assert record is not None
        assert record.key_value == key

    def test_returns_existing_secret(self, db_session):
        key1 = get_or_create_secret(db_session)
        key2 = get_or_create_secret(db_session)
        assert key1 == key2

    def test_custom_key_name(self, db_session):
        key = get_or_create_secret(db_session, key_name="custom_key")
        assert len(key) == 64
        record = (
            db_session.query(SystemSecretModel)
            .filter(SystemSecretModel.key_name == "custom_key")
            .first()
        )
        assert record is not None


class TestGetSecret:
    def test_returns_none_when_not_exists(self, db_session):
        result = get_secret(db_session, "nonexistent")
        assert result is None

    def test_returns_secret_value(self, db_session):
        get_or_create_secret(db_session)
        result = get_secret(db_session)
        assert result is not None
        assert len(result) == 64


class TestRotateSecret:
    def test_rotates_existing_secret(self, db_session):
        old_key = get_or_create_secret(db_session)
        new_key = rotate_secret(db_session)
        assert old_key != new_key
        assert len(new_key) == 64

        # 验证数据库已更新
        record = (
            db_session.query(SystemSecretModel)
            .filter(SystemSecretModel.key_name == DEFAULT_SECRET_KEY_NAME)
            .first()
        )
        assert record.key_value == new_key

    def test_creates_new_if_not_exists(self, db_session):
        new_key = rotate_secret(db_session)
        assert len(new_key) == 64
        record = (
            db_session.query(SystemSecretModel)
            .filter(SystemSecretModel.key_name == DEFAULT_SECRET_KEY_NAME)
            .first()
        )
        assert record is not None
