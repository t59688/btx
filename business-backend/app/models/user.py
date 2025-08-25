from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    openid = Column(String(100), unique=True, index=True, nullable=False)
    unionid = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)
    gender = Column(Integer, default=0)  # 0-未知，1-男，2-女
    country = Column(String(50), nullable=True)
    province = Column(String(50), nullable=True)
    city = Column(String(50), nullable=True)
    credits = Column(Integer, nullable=False, default=20)  # 用户积分余额
    is_blocked = Column(Boolean, default=False)  # 是否被封禁
    last_login_time = Column(DateTime, nullable=True)

    # 关系
    artworks = relationship("Artwork", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    credit_records = relationship("CreditRecord", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")