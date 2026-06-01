"""安全工具模块。

提供密码哈希、JWT Token 生成/验证等安全相关功能。
"""

import logging
from datetime import datetime, timedelta

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.core.secrets import get_or_create_secret

logger = logging.getLogger(__name__)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 延迟获取 SECRET_KEY，避免在导入时查询数据库
_SECRET_KEY: str | None = None


def get_secret_key(db: Session) -> str:
    """获取 JWT Secret Key（从数据库或自动生成）。"""
    global _SECRET_KEY
    if _SECRET_KEY is None:
        _SECRET_KEY = get_or_create_secret(db)
    return _SECRET_KEY


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码。"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码。"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(db: Session, data: dict, expires_delta: timedelta | None = None) -> str:
    """创建 JWT Access Token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    secret = get_secret_key(db)
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def create_refresh_token(db: Session, data: dict) -> str:
    """创建 JWT Refresh Token。"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    secret = get_secret_key(db)
    return jwt.encode(to_encode, secret, algorithm=ALGORITHM)


def decode_token(db: Session, token: str) -> dict | None:
    """解码并验证 JWT Token。"""
    try:
        secret = get_secret_key(db)
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
