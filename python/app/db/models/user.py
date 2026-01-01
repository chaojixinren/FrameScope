from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.db.engine import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=False)  # 存储bcrypt hash
    avatar = Column(String, nullable=True)
    is_online = Column(Integer, default=0)  # 0=离线, 1=在线
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系定义
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")

