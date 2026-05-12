from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import uuid
from src.core.config import get_settings

settings = get_settings()

class TokenData:
    """令牌数据"""
    def __init__(self, user_id: int):
        self.user_id = user_id

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire

def decode_token(token: str) -> Optional[TokenData]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=int(user_id))
    except JWTError:
        return None
