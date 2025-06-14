from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(Text)
    role = Column(String(50), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Record(Base):
    __tablename__ = "records"
    
    id = Column(String(36), primary_key=True, index=True)
    module = Column(String(100), index=True)
    data = Column(JSON)
    manager_on_duty = Column(String(255))
    submitted_by = Column(String(36), ForeignKey("users.id"))
    approval_status = Column(String(50), default="pending")
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    submitter = relationship("User", foreign_keys=[submitted_by])
    approver = relationship("User", foreign_keys=[approved_by])
