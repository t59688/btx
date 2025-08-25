from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.models.base_model import BaseModel


class SystemConfig(BaseModel):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True)
    config_value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True) 