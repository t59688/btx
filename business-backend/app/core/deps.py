from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.admin import Admin
from app.core.config import settings
from app.core.security import ALGORITHM
from app.schemas.token import TokenPayload

# OAuth2密码承载令牌，用于获取bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_STR}/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库获取用户
    user = db.query(User).get(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查用户是否被封禁
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被封禁"
        )
    
    return user


def get_optional_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    获取当前用户（可选，未认证时返回None）
    """
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (PyJWTError, ValidationError):
        return None
    
    # 从数据库获取用户
    user = db.query(User).get(token_data.sub)
    if not user or user.is_blocked:
        return None
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户（未被封禁）
    """
    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被封禁"
        )
    return current_user 


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    获取当前管理员用户
    """
    # 在数据库查询当前用户是否为管理员
    # 这里可以根据你的业务逻辑来判断用户是否有管理员权限
    # 例如：查询admin表，或检查用户的role字段等
    
    from app.db.session import get_db
    from sqlalchemy.orm import Session
    
    db = next(get_db())
    
    # 示例：检查user是否在admin表中存在
    admin = db.query(Admin).filter(Admin.user_id == current_user.id).first()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有足够的权限执行此操作",
        )
    
    return current_user 