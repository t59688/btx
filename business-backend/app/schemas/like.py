from typing import Optional
from pydantic import BaseModel
from datetime import datetime


# 基础点赞模型
class LikeBase(BaseModel):
    user_id: int
    artwork_id: int


# 创建点赞时的数据模型
class LikeCreate(LikeBase):
    pass


# 返回给API的点赞模型
class Like(LikeBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True 