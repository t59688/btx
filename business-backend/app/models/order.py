from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
import enum

from app.models.base_model import BaseModel


class OrderStatus(str, enum.Enum):
    PENDING = "pending"            # 待支付
    PAID = "paid"                  # 已支付
    COMPLETED = "completed"        # 已完成
    CANCELLED = "cancelled"        # 已取消
    REFUNDED = "refunded"          # 已退款


class Order(BaseModel):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_no = Column(String(50), unique=True, nullable=False, comment="订单编号")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")
    amount = Column(Float, nullable=False, comment="订单金额，单位元")
    credits = Column(Integer, nullable=False, comment="积分数量")
    status = Column(SQLEnum("pending", "paid", "completed", "cancelled", "refunded", name="order_status"), 
                    nullable=False, default="pending", comment="订单状态")
    payment_id = Column(String(100), nullable=True, comment="支付平台订单ID")
    payment_time = Column(DateTime, nullable=True, comment="支付时间")
    refund_time = Column(DateTime, nullable=True, comment="退款时间")
    remark = Column(String(255), nullable=True, comment="备注")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关系
    user = relationship("User", back_populates="orders")
    product = relationship("Product", backref="orders") 