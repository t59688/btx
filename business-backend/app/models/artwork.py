from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, func, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import enum

from app.models.base_model import BaseModel


class ArtworkStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Artwork(BaseModel):
    __tablename__ = "artworks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    style_id = Column(Integer, ForeignKey("styles.id", ondelete="RESTRICT"), nullable=False)
    source_image_url = Column(Text, nullable=False)
    result_image_url = Column(Text, nullable=True)
    status = Column(SQLEnum("processing", "completed", "failed", name="artwork_status"), 
                    nullable=False, default="processing")
    is_public = Column(Boolean, nullable=False, default=False)
    public_scope = Column(SQLEnum("result_only", "all", name="public_scope"), nullable=False, default="result_only")
    likes_count = Column(Integer, nullable=False, default=0)
    views_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    progress = Column(Integer, nullable=False, default=0)

    # 关系
    user = relationship("User", back_populates="artworks")
    style = relationship("Style", back_populates="artworks")
    likes = relationship("Like", back_populates="artwork", cascade="all, delete-orphan")

    @hybrid_property
    def style_name(self):
        return self.style.name if self.style else None

    def __repr__(self):
        return f"<Artwork(id={self.id}, user_id={self.user_id}, style_id={self.style_id}, status={self.status})>" 