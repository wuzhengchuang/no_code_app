from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uuid
from typing import Optional, Tuple
from src.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def _create_token(data: dict, token_type: str, expires_in: timedelta) -> Tuple[str, datetime]:
    """
    内部通用函数：创建JWT令牌

    Args:
        data: 要编码的数据
        token_type: 令牌类型 ("access" 或 "refresh")
        expires_in: 过期时间增量

    Returns:
        (token, expire_time) 元组
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + expires_in

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": token_type,
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    if expires_delta:
        return _create_token(data, "access", expires_delta)
    return _create_token(data, "access", timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS))

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    if expires_delta:
        return _create_token(data, "refresh", expires_delta)
    return _create_token(data, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
