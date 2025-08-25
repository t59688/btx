from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from app.models.base_model import BaseModel
import enum

class CardKeyStatus(enum.Enum):
    unused = "unused"
    used = "used"
    invalid = "invalid"

class CardKey(BaseModel):
    """卡密模型"""
    
    __tablename__ = "card_keys"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    card_key = Column(String(20), unique=True, index=True, nullable=False)
    credits = Column(Integer, nullable=False, comment="积分面值")
    batch_no = Column(String(50), index=True, nullable=True, comment="批次号")
    created_by = Column(Integer, nullable=True, comment="创建者ID")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    expired_at = Column(DateTime, nullable=True, comment="过期时间")
    status = Column(Enum(CardKeyStatus), default=CardKeyStatus.unused, nullable=False, comment="状态")
    used_at = Column(DateTime, nullable=True, comment="使用时间")
    used_by = Column(Integer, nullable=True, index=True, comment="使用者ID")
    used_by_nickname = Column(String(100), nullable=True, comment="使用者昵称")
    remark = Column(String(255), nullable=True, comment="备注") 