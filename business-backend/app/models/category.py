from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class StyleCategory(BaseModel):
    __tablename__ = "style_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(255), nullable=True)
    color = Column(String(50), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)

    # 关系
    styles = relationship("Style", back_populates="category") 