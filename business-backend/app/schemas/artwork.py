from typing import Optional, Literal
from pydantic import BaseModel, validator, model_validator
from datetime import datetime
from enum import Enum


# 作品状态枚举
class ArtworkStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 基础作品模型
class ArtworkBase(BaseModel):
    source_image_url: Optional[str] = None
    style_id: int
    is_public: bool = False


# 创建作品时的数据模型
class ArtworkCreate(ArtworkBase):
    pass


# 更新作品时的数据模型
class ArtworkUpdate(BaseModel):
    result_image_url: Optional[str] = None
    status: Optional[ArtworkStatus] = None
    error_message: Optional[str] = None


# 返回给API的作品模型
class Artwork(ArtworkBase):
    id: int
    user_id: int
    style_name: Optional[str] = None
    result_image_url: Optional[str] = None
    status: ArtworkStatus
    public_scope: Optional[str] = None
    likes_count: int
    views_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_liked_by_current_user: bool = False

    class Config:
        from_attributes = True


# 创建作品请求
class CreateArtworkRequest(BaseModel):
    style_id: int
    image_base64: Optional[str] = None  # Base64编码的图片数据，可选
    image_url: Optional[str] = None  # 图片URL，可选

    @model_validator(mode='after')
    def validate_image_source(self) -> 'CreateArtworkRequest':
        if not self.image_base64 and not self.image_url:
            raise ValueError('必须提供image_base64或image_url之一')
        return self


# 发布/取消发布作品请求
class PublishArtworkRequest(BaseModel):
    is_public: bool
    public_scope: Literal['result_only', 'all'] = 'result_only'

    @validator('public_scope')
    def scope_must_be_set_if_public(cls, v, values):
        if values.get('is_public') and not v:
            raise ValueError('当is_public为True时，public_scope必须提供')
        return v


# 作品列表查询参数
class ArtworkListParams(BaseModel):
    skip: int = 0
    limit: int = 10
    status: Optional[ArtworkStatus] = None
    is_public: Optional[bool] = None
    user_id: Optional[int] = None  # 筛选特定用户的作品
    style_id: Optional[int] = None  # 筛选特定风格的作品
    order_by: str = "created_at"  # 排序字段: created_at, likes_count, views_count
    order_desc: bool = True  # 排序方向: True为降序，False为升序 