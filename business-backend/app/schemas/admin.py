from typing import Optional
from pydantic import BaseModel
from datetime import datetime


# 基础管理员模型
class AdminBase(BaseModel):
    username: str


# 创建管理员时的数据模型
class AdminCreate(AdminBase):
    password: str


# 登录请求
class AdminLogin(BaseModel):
    username: str
    password: str


# 更新管理员信息
class AdminUpdate(BaseModel):
    password: Optional[str] = None


# 返回给API的管理员模型
class Admin(AdminBase):
    id: int
    created_at: datetime
    last_login_time: Optional[datetime] = None

    class Config:
        orm_mode = True


# 管理员登录响应
class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: Admin 