from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from app.models.credit_record import CreditRecordType


# 基础积分记录模型
class CreditRecordBase(BaseModel):
    user_id: int
    amount: int
    type: CreditRecordType
    description: Optional[str] = None
    related_id: Optional[int] = None


# 创建积分记录时的数据模型
class CreditRecordCreate(CreditRecordBase):
    balance: int  # 变动后余额


# 返回给API的积分记录模型
class CreditRecord(CreditRecordBase):
    id: int
    balance: int
    created_at: datetime

    class Config:
        from_attributes = True


# 广告奖励请求
class AdRewardRequest(BaseModel):
    ad_type: str  # 广告类型: rewarded_video, etc.


# 更新积分请求
class UpdateCreditsRequest(BaseModel):
    amount: int
    type: CreditRecordType
    description: Optional[str] = None
    related_id: Optional[int] = None 