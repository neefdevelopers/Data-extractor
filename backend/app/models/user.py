import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    role = Column(String(50), default="ADMIN")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
