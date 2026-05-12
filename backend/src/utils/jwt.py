import hashlib
from jose import jwt, JWTError
from typing import Optional
from src.core.config import get_settings

settings = get_settings()

def hash_token(token: str) -> str:
    """对令牌进行哈希处理，用于存储"""
    return hashlib.sha256(token.encode()).hexdigest()

def decode_token(token: str, verify_exp: bool = True) -> Optional[dict]:
    """解码令牌

    Args:
        token: JWT令牌
        verify_exp: 是否验证过期时间，默认验证
    """
    try:
        options = {}
        if not verify_exp:
            options["verify_exp"] = False

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options=options
        )
        return payload
    except JWTError:
        return None
