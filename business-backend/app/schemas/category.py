from typing import Optional
from pydantic import BaseModel
from datetime import datetime


# 基础分类模型
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int = 0


# 创建分类时的数据模型
class CategoryCreate(CategoryBase):
    pass


# 更新分类时的数据模型
class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


# 返回给API的分类模型
class Category(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 