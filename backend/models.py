from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Record(Base):
    __tablename__ = "records"
    
    id = Column(String, primary_key=True, index=True)
    module = Column(String, index=True)
    data = Column(JSON)
    manager_on_duty = Column(String)
    submitted_by = Column(String, ForeignKey("users.id"))
    approval_status = Column(String, default="pending")
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    submitter = relationship("User", foreign_keys=[submitted_by])
    approver = relationship("User", foreign_keys=[approved_by])
