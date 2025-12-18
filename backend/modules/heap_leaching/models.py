"""
Heap Leaching – Key Controls Data Models

Defines the SQLAlchemy ORM models for HeapConfig and BenchmarkConfig,
including versioning, change logging, and role-based access control.
"""

from sqlalchemy import (
    Column, String, Float, Date, DateTime, Integer, Text, ForeignKey, JSON,
    CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from uuid import uuid4


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid4())


class HeapConfig(Base):
    """
    Heap configuration model.
    
    Stores fixed engineering parameters for a single heap instance.
    One HeapConfig per module instance.
    Editable only by Admin or Management roles.
    Changes are versioned and timestamped.
    """
    __tablename__ = "heap_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_id = Column(String(100), unique=True, nullable=False, index=True)
    heap_tonnage_t = Column(Float, nullable=False)
    head_grade_gpt = Column(Float, nullable=False)
    leach_start_date = Column(Date, nullable=False)
    
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        CheckConstraint("heap_tonnage_t > 0", name="check_heap_tonnage_positive"),
        CheckConstraint("head_grade_gpt >= 0", name="check_head_grade_non_negative"),
    )


class HeapConfigHistory(Base):
    """
    Heap configuration version history.
    
    Stores previous versions of HeapConfig for audit trail.
    """
    __tablename__ = "heap_config_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), nullable=False, index=True)
    
    heap_id = Column(String(100), nullable=False)
    heap_tonnage_t = Column(Float, nullable=False)
    head_grade_gpt = Column(Float, nullable=False)
    leach_start_date = Column(Date, nullable=False)
    
    version = Column(Integer, nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    change_reason = Column(Text, nullable=True)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    changer = relationship("User", foreign_keys=[changed_by])


class BenchmarkConfig(Base):
    """
    Benchmark configuration model.
    
    Stores control limits and benchmark values for heap leaching operations.
    Benchmarks are mandatory before any operational data can be entered.
    Editable only by Admin role.
    All changes are logged with full audit trail.
    """
    __tablename__ = "benchmark_configs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), unique=True, nullable=False, index=True)
    
    application_rate_min_L_m2_hr = Column(Float, nullable=False)
    application_rate_max_L_m2_hr = Column(Float, nullable=False)
    cn_min_ppm = Column(Float, nullable=False)
    cn_max_ppm = Column(Float, nullable=False)
    ph_min = Column(Float, nullable=False)
    ph_max = Column(Float, nullable=False)
    pls_return_min_pct = Column(Float, nullable=False)
    pond_freeboard_min_m = Column(Float, nullable=False)
    cn_consumption_max_kgpt = Column(Float, nullable=False)
    cn_efficiency_min_gpkg = Column(Float, nullable=False)
    pls_low_au_mgL = Column(Float, nullable=False)
    
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        CheckConstraint(
            "application_rate_min_L_m2_hr < application_rate_max_L_m2_hr",
            name="check_application_rate_min_lt_max"
        ),
        CheckConstraint(
            "cn_min_ppm < cn_max_ppm",
            name="check_cn_min_lt_max"
        ),
        CheckConstraint(
            "ph_min < ph_max",
            name="check_ph_min_lt_max"
        ),
        CheckConstraint(
            "ph_min >= 10.0",
            name="check_ph_min_gte_10"
        ),
        CheckConstraint(
            "pond_freeboard_min_m > 0",
            name="check_pond_freeboard_positive"
        ),
    )


class BenchmarkChangeLog(Base):
    """
    Benchmark configuration change log.
    
    Logs all changes to benchmark values with full audit trail including:
    - previous value
    - new value
    - user who made the change
    - timestamp
    - reason for change
    """
    __tablename__ = "benchmark_change_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    benchmark_config_id = Column(String(36), ForeignKey("benchmark_configs.id"), nullable=False, index=True)
    
    field_name = Column(String(100), nullable=False)
    previous_value = Column(Float, nullable=True)
    new_value = Column(Float, nullable=False)
    
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    change_reason = Column(Text, nullable=False)
    
    benchmark_config = relationship("BenchmarkConfig", foreign_keys=[benchmark_config_id])
    changer = relationship("User", foreign_keys=[changed_by])


class DailyControlLog(Base):
    """
    Daily control log for heap leaching operations.
    
    Captures minimum operational measurements required to control heap leaching.
    Records are IMMUTABLE after submission - no edits or deletions permitted.
    
    Access Control:
    - Contractor role: may create new records only
    - Engineer/Management/Admin roles: read-only access
    
    One record per calendar day per heap.
    """
    __tablename__ = "daily_control_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), nullable=False, index=True)
    
    log_date = Column(Date, nullable=False, index=True)
    area_irrigated_m2 = Column(Float, nullable=False)
    flow_m3_per_hr = Column(Float, nullable=False)
    irrigation_hours = Column(Float, nullable=False)
    applied_cn_ppm = Column(Float, nullable=False)
    applied_ph = Column(Float, nullable=False)
    pls_flow_m3 = Column(Float, nullable=False)
    pls_au_mgL = Column(Float, nullable=False)
    pond_freeboard_m = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        UniqueConstraint("heap_config_id", "log_date", name="uq_daily_control_log_heap_date"),
        CheckConstraint("area_irrigated_m2 >= 0", name="check_area_irrigated_non_negative"),
        CheckConstraint("flow_m3_per_hr >= 0", name="check_flow_non_negative"),
        CheckConstraint("irrigation_hours >= 0", name="check_irrigation_hours_non_negative"),
        CheckConstraint("irrigation_hours <= 24", name="check_irrigation_hours_max_24"),
        CheckConstraint("applied_cn_ppm >= 0", name="check_applied_cn_non_negative"),
        CheckConstraint("applied_ph >= 0", name="check_applied_ph_min"),
        CheckConstraint("applied_ph <= 14", name="check_applied_ph_max"),
        CheckConstraint("pls_flow_m3 >= 0", name="check_pls_flow_non_negative"),
        CheckConstraint("pls_au_mgL >= 0", name="check_pls_au_non_negative"),
        CheckConstraint("pond_freeboard_m >= 0", name="check_pond_freeboard_non_negative"),
    )
