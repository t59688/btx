from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.schemas.category import Category


# 基础风格模型
class StyleBase(BaseModel):
    name: str
    description: Optional[str] = None
    preview_url: Optional[str] = None
    reference_image_url: Optional[str] = None
    category_id: Optional[int] = None
    prompt: Optional[str] = None
    credits_cost: int = 10
    sort_order: int = 0


# 创建风格时的数据模型
class StyleCreate(StyleBase):
    category: Optional[str] = None


# 更新风格时的数据模型
class StyleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    reference_image_url: Optional[str] = None
    category_id: Optional[int] = None
    prompt: Optional[str] = None
    credits_cost: Optional[int] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# 返回给API的风格模型
class Style(StyleBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category_info: Optional[Category] = Field(None, validation_alias='category')

    class Config:
        orm_mode = True
        allow_population_by_field_name = True 