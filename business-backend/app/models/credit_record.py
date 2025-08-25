from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base_model import BaseModel


class CreditRecordType(str, enum.Enum):
    CREATE = "create"            # 创建作品
    AD_REWARD = "ad_reward"      # 广告奖励
    ADMIN_ADJUSTMENT = "admin_adjustment"  # 管理员调整
    OTHER = "other"              # 其他
    CARD_KEY = "card_key"        # 卡密兑换
    REGISTER = "register"        # 注册赠送
    GENERATE = "generate"        # 生成AI作品
    PURCHASE = "purchase"        # 购买积分
    REFUND = "refund"            # 退款


class CreditRecord(BaseModel):
    __tablename__ = "credit_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)  # 正为增加，负为减少
    balance = Column(Integer, nullable=False)  # 变动后余额
    type = Column(SQLEnum("create", "ad_reward", "admin_adjustment", "other",
                          "card_key", "register", "generate", "purchase", "refund", 
                          name="credit_record_type"), 
                  nullable=False)
    description = Column(String(255), nullable=True)
    related_id = Column(Integer, nullable=True)  # 相关ID，如作品ID

    # 关系
    user = relationship("User", back_populates="credit_records") 