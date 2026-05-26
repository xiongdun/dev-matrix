"""系统密钥管理模块。

提供 JWT Secret 等系统级密钥的自动生成、安全存储和读取功能。
首次启动时自动生成 256 位随机密钥并持久化到数据库，后续复用。
"""

import secrets
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.state.models import SystemSecretModel

logger = logging.getLogger(__name__)

DEFAULT_SECRET_KEY_NAME = "jwt_secret_key"
SECRET_KEY_LENGTH = 64  # 512 bits


def generate_secret_key(length: int = SECRET_KEY_LENGTH) -> str:
    """生成加密安全的随机密钥。

    Args:
        length: 密钥字符长度，默认 64（512 bits）。

    Returns:
        str: 十六进制编码的随机密钥。
    """
    return secrets.token_hex(length // 2)


def get_or_create_secret(db: Session, key_name: str = DEFAULT_SECRET_KEY_NAME) -> str:
    """获取或创建系统密钥。

    如果数据库中已存在该密钥，直接返回；否则生成新密钥并保存。

    Args:
        db: 数据库会话。
        key_name: 密钥名称。

    Returns:
        str: 密钥值。
    """
    secret = db.query(SystemSecretModel).filter(SystemSecretModel.key_name == key_name).first()
    if secret:
        return secret.key_value

    # 生成新密钥
    new_key = generate_secret_key()
    secret = SystemSecretModel(key_name=key_name, key_value=new_key)
    db.add(secret)
    db.commit()
    logger.info("Generated new system secret: %s", key_name)
    return new_key


def get_secret(db: Session, key_name: str = DEFAULT_SECRET_KEY_NAME) -> Optional[str]:
    """获取系统密钥。

    Args:
        db: 数据库会话。
        key_name: 密钥名称。

    Returns:
        Optional[str]: 密钥值，不存在则返回 None。
    """
    secret = db.query(SystemSecretModel).filter(SystemSecretModel.key_name == key_name).first()
    return secret.key_value if secret else None


def rotate_secret(db: Session, key_name: str = DEFAULT_SECRET_KEY_NAME) -> str:
    """轮换系统密钥。

    生成新密钥并更新数据库。注意：轮换后所有已颁发的 Token 将失效。

    Args:
        db: 数据库会话。
        key_name: 密钥名称。

    Returns:
        str: 新密钥值。
    """
    new_key = generate_secret_key()
    secret = db.query(SystemSecretModel).filter(SystemSecretModel.key_name == key_name).first()
    if secret:
        secret.key_value = new_key
    else:
        secret = SystemSecretModel(key_name=key_name, key_value=new_key)
        db.add(secret)
    db.commit()
    logger.warning("Rotated system secret: %s. All existing tokens are now invalid.", key_name)
    return new_key
