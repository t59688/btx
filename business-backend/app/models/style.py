from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class Style(BaseModel):
    __tablename__ = "styles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    preview_url = Column(Text, nullable=True)
    reference_image_url = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    category_id = Column(Integer, ForeignKey('style_categories.id'), nullable=True)
    prompt = Column(Text, nullable=True)
    credits_cost = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, nullable=False, default=0)

    # 关系
    artworks = relationship("Artwork", back_populates="style")
    category = relationship("StyleCategory", back_populates="styles") 