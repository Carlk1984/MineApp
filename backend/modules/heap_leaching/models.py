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


class ControlRuleLog(Base):
    """
    Control rule log for hard stops and soft alerts.
    
    Records are IMMUTABLE - logs all triggered control rules with full audit trail.
    
    Rule Types:
    - HARD_STOP: Blocks submission/operation (e.g., HS-1, HS-2)
    - SOFT_ALERT: Flags issue but allows submission (e.g., SA-1, SA-2, SA-3, SA-4)
    
    Each log entry includes:
    - Rule ID (e.g., HS-1, SA-1)
    - Rule type (HARD_STOP or SOFT_ALERT)
    - Triggering value(s)
    - Benchmark value(s)
    - Date and DailyControlLog reference
    """
    __tablename__ = "control_rule_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), nullable=False, index=True)
    daily_control_log_id = Column(String(36), ForeignKey("daily_control_logs.id"), nullable=True, index=True)
    
    rule_id = Column(String(20), nullable=False, index=True)
    rule_type = Column(String(20), nullable=False, index=True)
    rule_message = Column(Text, nullable=False)
    
    triggering_field = Column(String(100), nullable=False)
    triggering_value = Column(Float, nullable=False)
    benchmark_field = Column(String(100), nullable=True)
    benchmark_value = Column(Float, nullable=True)
    
    log_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    daily_control_log = relationship("DailyControlLog", foreign_keys=[daily_control_log_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('HARD_STOP', 'SOFT_ALERT', 'WEEKLY_FLAG')",
            name="check_rule_type_valid"
        ),
    )


class WeeklyControlSummary(Base):
    """
    Weekly control summary for heap leaching operations.
    
    Provides management-level weekly KPIs for economics and efficiency.
    Aggregates data from DailyControlLog records for the week.
    
    Keys:
    - heap_config_id (FK to HeapConfig)
    - week_start_date (Monday-based ISO week start)
    - week_end_date
    
    Manual Input:
    - cn_used_kg: Total NaCN used during the week
    
    System-generated aggregated fields (read-only):
    - weekly_solution_applied_m3
    - weekly_pls_flow_m3
    - weekly_gold_in_pls_g
    - cumulative_gold_in_pls_g
    - contained_gold_g
    - recovery_pct
    - cn_consumption_kgpt
    - cn_efficiency_gpkg
    
    One WeeklyControlSummary per heap per week.
    Summaries are immutable after approval.
    """
    __tablename__ = "weekly_control_summaries"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), nullable=False, index=True)
    
    week_start_date = Column(Date, nullable=False, index=True)
    week_end_date = Column(Date, nullable=False, index=True)
    
    cn_used_kg = Column(Float, nullable=False)
    
    weekly_solution_applied_m3 = Column(Float, nullable=False)
    weekly_pls_flow_m3 = Column(Float, nullable=False)
    weekly_gold_in_pls_g = Column(Float, nullable=False)
    
    cumulative_gold_in_pls_g = Column(Float, nullable=False)
    contained_gold_g = Column(Float, nullable=True)
    recovery_pct = Column(Float, nullable=True)
    
    cn_consumption_kgpt = Column(Float, nullable=True)
    cn_efficiency_gpkg = Column(Float, nullable=True)
    
    is_approved = Column(Integer, default=0, nullable=False)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        UniqueConstraint("heap_config_id", "week_start_date", name="uq_weekly_summary_heap_week"),
        CheckConstraint("cn_used_kg >= 0", name="check_cn_used_non_negative"),
        CheckConstraint("weekly_solution_applied_m3 >= 0", name="check_weekly_solution_non_negative"),
        CheckConstraint("weekly_pls_flow_m3 >= 0", name="check_weekly_pls_non_negative"),
        CheckConstraint("weekly_gold_in_pls_g >= 0", name="check_weekly_gold_non_negative"),
        CheckConstraint("week_end_date >= week_start_date", name="check_week_end_gte_start"),
    )


class StopLeachDecision(Base):
    """
    Stop-Leach decision record for heap leaching operations.
    
    System-generated decision based on weekly economic metrics.
    Records are IMMUTABLE - represents the system's recommendation.
    
    Decision Logic:
    - stop_recommendation = TRUE if economic thresholds are breached
    - Original decision cannot be modified or deleted
    - Management can create an override (StopLeachOverride) but decision remains
    
    One StopLeachDecision per WeeklyControlSummary.
    """
    __tablename__ = "stop_leach_decisions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), nullable=False, index=True)
    weekly_summary_id = Column(String(36), ForeignKey("weekly_control_summaries.id"), unique=True, nullable=False, index=True)
    
    decision_date = Column(Date, nullable=False, index=True)
    stop_recommendation = Column(Integer, nullable=False)
    
    recovery_pct = Column(Float, nullable=True)
    cn_efficiency_gpkg = Column(Float, nullable=True)
    cn_consumption_kgpt = Column(Float, nullable=True)
    cumulative_gold_in_pls_g = Column(Float, nullable=True)
    
    decision_reasons = Column(JSON, nullable=False)
    
    system_status = Column(String(50), nullable=False, default="PENDING")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    weekly_summary = relationship("WeeklyControlSummary", foreign_keys=[weekly_summary_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        CheckConstraint(
            "stop_recommendation IN (0, 1)",
            name="check_stop_recommendation_boolean"
        ),
        CheckConstraint(
            "system_status IN ('PENDING', 'CONTINUE', 'STOP', 'CONTINUE_UNDER_OVERRIDE', 'STOP_CONFIRMED_BY_MANAGEMENT')",
            name="check_system_status_valid"
        ),
    )


class StopLeachOverride(Base):
    """
    Management override for Stop-Leach decisions.
    
    Allows management to override system STOP recommendations.
    Overrides are additive - original decision remains immutable.
    
    Rules:
    - One override allowed per StopLeachDecision
    - Overrides cannot be edited or deleted once submitted
    - Overrides can only be created by Management role
    - Original StopLeachDecision remains immutable
    
    Override Actions:
    - CONTINUE: System status becomes "CONTINUE_UNDER_OVERRIDE"
    - STOP: System status becomes "STOP_CONFIRMED_BY_MANAGEMENT"
    """
    __tablename__ = "stop_leach_overrides"
    
    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    heap_config_id = Column(String(36), ForeignKey("heap_configs.id"), nullable=False, index=True)
    decision_id = Column(String(36), ForeignKey("stop_leach_decisions.id"), unique=True, nullable=False, index=True)
    
    override_action = Column(String(20), nullable=False)
    override_reason = Column(String(100), nullable=False)
    override_justification_text = Column(Text, nullable=False)
    
    decision_snapshot = Column(JSON, nullable=False)
    
    override_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    override_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    heap_config = relationship("HeapConfig", foreign_keys=[heap_config_id])
    decision = relationship("StopLeachDecision", foreign_keys=[decision_id])
    overrider = relationship("User", foreign_keys=[override_by])
    
    __table_args__ = (
        CheckConstraint(
            "override_action IN ('CONTINUE', 'STOP')",
            name="check_override_action_valid"
        ),
        CheckConstraint(
            "override_reason IN ('SHORT_TERM_OPERATIONAL_DISRUPTION', 'TEMPORARY_REAGENT_SUPPLY_ISSUE', 'EXPECTED_DELAYED_RECOVERY', 'STRATEGIC_DECISION', 'TRIAL_TEST_CONTINUATION', 'OTHER')",
            name="check_override_reason_valid"
        ),
        CheckConstraint(
            "length(override_justification_text) >= 50",
            name="check_justification_min_length"
        ),
    )
