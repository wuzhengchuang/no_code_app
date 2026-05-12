from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.user import User
from src.schemas.user import UserResponse, UserProfileUpdate, UserPasswordUpdate
from src.core.security import verify_password, get_password_hash

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user

    def get_user_by_email(self, email: str) -> User:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user

    def update_profile(self, user_id: int, data: UserProfileUpdate) -> UserResponse:
        user = self.get_user_by_id(user_id)
        
        if data.nickname is not None:
            user.nickname = data.nickname
        if data.avatarUrl is not None:
            user.avatar_url = data.avatarUrl
        
        self.db.commit()
        self.db.refresh(user)

        return UserResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatarUrl=user.avatar_url,
            status=user.status,
            lastLoginAt=user.last_login_at,
            createdAt=user.created_at,
            updatedAt=user.updated_at
        )

    def update_password(self, user_id: int, data: UserPasswordUpdate) -> None:
        user = self.get_user_by_id(user_id)
        
        if not verify_password(data.oldPassword, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="旧密码不正确"
            )
        
        user.password_hash = get_password_hash(data.newPassword)
        self.db.commit()

    def get_user_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            avatarUrl=user.avatar_url,
            status=user.status,
            lastLoginAt=user.last_login_at,
            createdAt=user.created_at,
            updatedAt=user.updated_at
        )
