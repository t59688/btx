from sqlalchemy import Column, Integer, String, DateTime, func

from app.models.base_model import BaseModel


class Admin(BaseModel):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(50), nullable=False)
    last_login_time = Column(DateTime, nullable=True) 