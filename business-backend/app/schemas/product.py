from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# 基础商品模型
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    credits: int
    price: float
    image_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


# 创建商品时的数据模型
class ProductCreate(ProductBase):
    pass


# 更新商品时的数据模型
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# 返回给API的商品模型
class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 