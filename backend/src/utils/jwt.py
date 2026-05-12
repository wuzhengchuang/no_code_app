import hashlib
from jose import jwt, JWTError
from typing import Optional
from src.core.config import get_settings

settings = get_settings()

def hash_token(token: str) -> str:
    """对令牌进行哈希处理，用于存储"""
    return hashlib.sha256(token.encode()).hexdigest()

def decode_token(token: str) -> Optional[dict]:
    """解码令牌"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        return payload
    except JWTError:
        return None
