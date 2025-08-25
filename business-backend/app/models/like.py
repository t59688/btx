from sqlalchemy import Column, Integer, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel


class Like(BaseModel):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    artwork_id = Column(Integer, ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False)

    # 唯一约束：用户只能点赞一次
    __table_args__ = (
        UniqueConstraint('user_id', 'artwork_id', name='uk_user_artwork'),
    )

    # 关系
    user = relationship("User", back_populates="likes")
    artwork = relationship("Artwork", back_populates="likes") 