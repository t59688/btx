from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, func
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class Product(BaseModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="商品名称")
    description = Column(Text, nullable=True, comment="商品描述")
    credits = Column(Integer, nullable=False, comment="积分数量")
    price = Column(Float, nullable=False, comment="价格，单位元")
    image_url = Column(Text, nullable=True, comment="商品图片URL")
    is_active = Column(Boolean, default=True, comment="是否上架")
    sort_order = Column(Integer, default=0, comment="排序值")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间") 