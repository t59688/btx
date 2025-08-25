from sqlalchemy import Column, Boolean, DateTime, func
from app.db.session import Base


class BaseModel(Base):
    """
    所有模型的基类，包含通用字段和软删除功能
    """
    __abstract__ = True

    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now()) 