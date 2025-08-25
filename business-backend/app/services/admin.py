from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import hashlib
import os
import secrets

from app.core.config import settings
from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, Admin as AdminSchema, AdminUpdate
from app.db.utils import get_base_query, soft_delete

# 安全相关配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30天

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/super/login")


class AdminService:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        if plain_password == hashed_password:
            return True
        # 首先尝试使用MD5验证（适用于初始管理员账号）
        md5_hash = hashlib.md5(plain_password.encode()).hexdigest()
        if md5_hash == hashed_password:
            return True
        
        # 如果MD5验证失败，尝试使用bcrypt验证（适用于后续创建的账号）
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    @staticmethod
    def get_password_hash(password):
        # 使用bcrypt为新创建的管理员生成密码哈希
        return pwd_context.hash(password)

    @staticmethod
    def get_admin_by_username(db: Session, username: str):
        return get_base_query(db, Admin).filter(Admin.username == username).first()

    @staticmethod
    def get_admin(db: Session, admin_id: int):
        return get_base_query(db, Admin).filter(Admin.id == admin_id).first()

    @staticmethod
    def create_admin(db: Session, admin: AdminCreate):
        hashed_password = AdminService.get_password_hash(admin.password)
        db_admin = Admin(
            username=admin.username,
            password_hash=hashed_password,
            salt="default_salt",  # 可以实现更安全的盐生成
        )
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        return db_admin

    @staticmethod
    def update_admin(db: Session, admin_id: int, admin: AdminUpdate):
        db_admin = AdminService.get_admin(db, admin_id)
        if not db_admin:
            return None
        
        update_data = admin.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = AdminService.get_password_hash(update_data.pop("password"))
        
        for key, value in update_data.items():
            setattr(db_admin, key, value)
        
        db.commit()
        db.refresh(db_admin)
        return db_admin

    @staticmethod
    def authenticate_admin(db: Session, username: str, password: str):
        admin = AdminService.get_admin_by_username(db, username)
        if not admin:
            return False
        if not AdminService.verify_password(password, admin.password_hash):
            return False
        return admin

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def update_admin_login_time(db: Session, admin_id: int):
        db_admin = AdminService.get_admin(db, admin_id)
        if db_admin:
            db_admin.last_login_time = datetime.utcnow()
            db.commit()
            db.refresh(db_admin)
        return db_admin

    @staticmethod
    async def get_current_admin(
        token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
    ):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的身份验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            admin_id: str = payload.get("sub")
            if admin_id is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        admin = AdminService.get_admin(db, admin_id=int(admin_id))
        if admin is None:
            raise credentials_exception
        return admin

    @staticmethod
    def get_admins(db: Session, skip: int = 0, limit: int = 100) -> List[Admin]:
        return get_base_query(db, Admin).offset(skip).limit(limit).all()

    @staticmethod
    def delete_admin(db: Session, admin_id: int) -> bool:
        db_admin = AdminService.get_admin(db, admin_id)
        if db_admin:
            # 软删除记录
            return soft_delete(db, db_admin)
        return False 