from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status

from src.models.user import User, UserSession
from src.schemas.auth import UserRegister, UserLogin, TokenResponse, AuthResponse
from src.schemas.user import UserResponse
from src.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token
)
from src.utils.jwt import hash_token
from src.utils.security import validate_password_strength

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_password(self, password: str) -> bool:
        return validate_password_strength(password)

    def _detect_device_type(self, user_agent: Optional[str]) -> Optional[str]:
        if not user_agent:
            return None
        user_agent = user_agent.lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'desktop' in user_agent or 'windows' in user_agent or 'macintosh' in user_agent:
            return 'desktop'
        return 'web'

    def register(self, data: UserRegister) -> AuthResponse:
        if not self._validate_password(data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码强度不足，至少8位，包含字母和数字"
            )

        existing_user = self.db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户已存在"
            )

        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            nickname=data.nickname,
            status=1
        )
        self.db.add(user)
        self.db.flush()

        token_data = {"sub": str(user.id), "email": user.email}
        access_token, access_expire = create_access_token(token_data)
        refresh_token, refresh_expire = create_refresh_token(token_data)

        session = UserSession(
            user_id=user.id,
            token=hash_token(access_token),
            refresh_token=hash_token(refresh_token),
            expires_at=access_expire,
            refresh_expires_at=refresh_expire
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(user)

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatarUrl=user.avatar_url,
            status=user.status,
            lastLoginAt=user.last_login_at,
            createdAt=user.created_at,
            updatedAt=user.updated_at
        )

        return AuthResponse(
            token=access_token,
            refreshToken=refresh_token,
            expiresAt=access_expire,
            refreshExpiresAt=refresh_expire,
            user=user_response
        )

    def login(self, data: UserLogin, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuthResponse:
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误"
            )

        if user.status != 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已被禁用"
            )

        user.last_login_at = datetime.utcnow()
        device_type = self._detect_device_type(user_agent)

        token_data = {"sub": str(user.id), "email": user.email}
        access_token, access_expire = create_access_token(token_data)
        refresh_token, refresh_expire = create_refresh_token(token_data)

        session = UserSession(
            user_id=user.id,
            token=hash_token(access_token),
            refresh_token=hash_token(refresh_token),
            expires_at=access_expire,
            refresh_expires_at=refresh_expire,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            device_type=device_type
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(user)

        user_response = UserResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatarUrl=user.avatar_url,
            status=user.status,
            lastLoginAt=user.last_login_at,
            createdAt=user.created_at,
            updatedAt=user.updated_at
        )

        return AuthResponse(
            token=access_token,
            refreshToken=refresh_token,
            expiresAt=access_expire,
            refreshExpiresAt=refresh_expire,
            user=user_response
        )

    def refresh_token(self, refresh_token: str) -> TokenResponse:
        from src.utils.jwt import decode_token

        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )

        hashed_refresh_token = hash_token(refresh_token)
        session = self.db.query(UserSession).filter(
            UserSession.refresh_token == hashed_refresh_token,
            UserSession.is_revoked == 0
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌不存在或已撤销"
            )

        if session.refresh_expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌已过期"
            )

        user = self.db.query(User).filter(User.id == session.user_id).first()
        if not user or user.status != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )

        session.is_revoked = 1

        token_data = {"sub": str(user.id), "email": user.email}
        new_access_token, new_access_expire = create_access_token(token_data)
        new_refresh_token, new_refresh_expire = create_refresh_token(token_data)

        new_session = UserSession(
            user_id=user.id,
            token=hash_token(new_access_token),
            refresh_token=hash_token(new_refresh_token),
            expires_at=new_access_expire,
            refresh_expires_at=new_refresh_expire,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_type=session.device_type
        )
        self.db.add(new_session)
        self.db.commit()

        return TokenResponse(
            token=new_access_token,
            refreshToken=new_refresh_token,
            expiresAt=new_access_expire,
            refreshExpiresAt=new_refresh_expire
        )

    def logout(self, token: str, refresh_token: str) -> None:
        hashed_token = hash_token(token)
        hashed_refresh_token = hash_token(refresh_token)

        session = self.db.query(UserSession).filter(
            UserSession.token == hashed_token,
            UserSession.is_revoked == 0
        ).first()

        if session:
            session.is_revoked = 1

        refresh_session = self.db.query(UserSession).filter(
            UserSession.refresh_token == hashed_refresh_token,
            UserSession.is_revoked == 0
        ).first()

        if refresh_session:
            refresh_session.is_revoked = 1

        self.db.commit()

    def get_sessions(self, user_id: int) -> list:
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_revoked == 0
        ).order_by(UserSession.created_at.desc()).all()
        return sessions

    def revoke_session(self, user_id: int, session_id: int) -> None:
        session = self.db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        session.is_revoked = 1
        self.db.commit()
