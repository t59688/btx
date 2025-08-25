from typing import Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


# 基础用户模型
class UserBase(BaseModel):
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = 0
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None


# 创建用户时的数据模型
class UserCreate(UserBase):
    pass


# 更新用户时的数据模型
class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None


# 返回给API的用户模型
class User(UserBase):
    id: int
    credits: int
    is_blocked: bool
    created_at: datetime
    updated_at: datetime
    last_login_time: Optional[datetime] = None

    class Config:
        orm_mode = True


# 微信登录请求
class WechatLoginRequest(BaseModel):
    code: str
    user_info: Optional[dict] = None


# 微信登录响应
class WechatLoginResponse(BaseModel):
    access_token: str
    user: User 