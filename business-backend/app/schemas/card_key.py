from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
import random
import string

# 卡密状态枚举
class CardKeyStatus:
    UNUSED = "unused"
    USED = "used"
    INVALID = "invalid"

# 卡密基础模型
class CardKeyBase(BaseModel):
    credits: int = Field(..., description="积分面值")
    batch_no: Optional[str] = Field(None, description="批次号")
    expired_at: Optional[datetime] = Field(None, description="过期时间")
    remark: Optional[str] = Field(None, description="备注")

# 创建卡密请求模型
class CardKeyCreate(CardKeyBase):
    count: int = Field(..., gt=0, le=1000, description="创建数量")
    
    @validator('count')
    def validate_count(cls, v):
        if v <= 0 or v > 1000:
            raise ValueError('创建数量必须在1-1000之间')
        return v

# 卡密模型（数据库返回）
class CardKey(CardKeyBase):
    id: int
    card_key: str
    created_by: Optional[int] = None
    created_at: datetime
    status: str
    used_at: Optional[datetime] = None
    used_by: Optional[int] = None
    used_by_nickname: Optional[str] = None
    
    class Config:
        from_attributes = True

# 卡密列表查询参数
class CardKeyListParams(BaseModel):
    skip: int = 0
    limit: int = 10
    status: Optional[str] = None
    batch_no: Optional[str] = None
    created_start: Optional[datetime] = None
    created_end: Optional[datetime] = None
    order_by: str = "created_at"
    order_desc: bool = True

# 更新卡密状态请求
class CardKeyStatusUpdate(BaseModel):
    status: str = Field(..., description="状态: unused, used, invalid")

# 卡密激活请求
class CardKeyActivate(BaseModel):
    card_key: str = Field(..., min_length=9, max_length=9, description="卡密")
    
    @validator('card_key')
    def validate_card_key(cls, v):
        if not all(c in string.ascii_uppercase + string.digits for c in v):
            raise ValueError('卡密只能包含大写字母和数字')
        return v

# 卡密生成器
def generate_card_key() -> str:
    """生成9位数字和大写字母组成的卡密"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(9))

# 卡密批量创建响应
class CardKeyBatchCreateResponse(BaseModel):
    batch_no: str
    count: int
    credits: int
    expired_at: Optional[datetime] = None 

# 定义用于列表返回的包装模型
class CardKeyListResponse(BaseModel):
    items: List[CardKey]
    total: int
    page: int
    per_page: int
    total_pages: int