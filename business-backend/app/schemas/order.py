from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.order import OrderStatus


# 基础订单模型
class OrderBase(BaseModel):
    user_id: int
    product_id: int
    amount: float
    credits: int
    status: Optional[OrderStatus] = OrderStatus.PENDING
    remark: Optional[str] = None


# 创建订单时的数据模型
class OrderCreate(OrderBase):
    pass


# 更新订单时的数据模型
class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_id: Optional[str] = None
    payment_time: Optional[datetime] = None
    refund_time: Optional[datetime] = None
    remark: Optional[str] = None


# 返回给API的订单模型
class Order(OrderBase):
    id: int
    order_no: str
    payment_id: Optional[str] = None
    payment_time: Optional[datetime] = None
    refund_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 订单详情模型（包含商品信息）
class OrderDetail(Order):
    product_name: str
    product_description: Optional[str] = None
    product_image_url: Optional[str] = None

    class Config:
        from_attributes = True


# 创建支付请求模型
class CreatePaymentRequest(BaseModel):
    product_id: int


# 支付回调请求模型
class PaymentCallbackRequest(BaseModel):
    order_no: str
    payment_id: str
    status: str
    amount: float 