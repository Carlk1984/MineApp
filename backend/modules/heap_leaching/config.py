"""
Heap Leaching – Key Controls Configuration Schema

Defines the Pydantic schemas for HeapConfig and BenchmarkConfig,
including request/response models and validation rules.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class OreType(str, Enum):
    """Supported ore types for heap leaching."""
    OXIDE_GOLD = "oxide_gold"


class RecoveryMethod(str, Enum):
    """Supported recovery methods."""
    SOLUTION_BASED_PLS = "solution_based_pls"


class HeapConfigCreate(BaseModel):
    """Request schema for creating a HeapConfig."""
    
    heap_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the heap instance"
    )
    heap_tonnage_t: float = Field(
        ...,
        gt=0,
        description="Heap tonnage in tonnes (must be positive)"
    )
    head_grade_gpt: float = Field(
        ...,
        ge=0,
        description="Head grade in grams per tonne (must be non-negative)"
    )
    leach_start_date: date = Field(
        ...,
        description="Start date for heap leaching operations"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "heap_id": "HEAP-20241217-ABC12",
                "heap_tonnage_t": 1000.0,
                "head_grade_gpt": 2.5,
                "leach_start_date": "2024-12-17"
            }
        }


class HeapConfigUpdate(BaseModel):
    """Request schema for updating a HeapConfig."""
    
    heap_tonnage_t: Optional[float] = Field(
        default=None,
        gt=0,
        description="Heap tonnage in tonnes (must be positive)"
    )
    head_grade_gpt: Optional[float] = Field(
        default=None,
        ge=0,
        description="Head grade in grams per tonne (must be non-negative)"
    )
    leach_start_date: Optional[date] = Field(
        default=None,
        description="Start date for heap leaching operations"
    )
    change_reason: Optional[str] = Field(
        default=None,
        description="Reason for the configuration change"
    )


class HeapConfigResponse(BaseModel):
    """Response schema for HeapConfig."""
    
    id: str
    heap_id: str
    heap_tonnage_t: float
    head_grade_gpt: float
    leach_start_date: date
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    class Config:
        from_attributes = True


class BenchmarkConfigCreate(BaseModel):
    """Request schema for creating a BenchmarkConfig."""
    
    application_rate_min_L_m2_hr: float = Field(
        ...,
        gt=0,
        description="Minimum application rate in L/m²/hr"
    )
    application_rate_max_L_m2_hr: float = Field(
        ...,
        gt=0,
        description="Maximum application rate in L/m²/hr"
    )
    cn_min_ppm: float = Field(
        ...,
        ge=0,
        description="Minimum cyanide concentration in ppm"
    )
    cn_max_ppm: float = Field(
        ...,
        gt=0,
        description="Maximum cyanide concentration in ppm"
    )
    ph_min: float = Field(
        ...,
        ge=10.0,
        description="Minimum pH (must be >= 10.0)"
    )
    ph_max: float = Field(
        ...,
        gt=10.0,
        description="Maximum pH"
    )
    pls_return_min_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Minimum PLS return percentage"
    )
    pond_freeboard_min_m: float = Field(
        ...,
        gt=0,
        description="Minimum pond freeboard in meters (must be > 0)"
    )
    cn_consumption_max_kgpt: float = Field(
        ...,
        gt=0,
        description="Maximum cyanide consumption in kg per tonne"
    )
    cn_efficiency_min_gpkg: float = Field(
        ...,
        gt=0,
        description="Minimum cyanide efficiency in grams per kg"
    )
    pls_low_au_mgL: float = Field(
        ...,
        ge=0,
        description="Low PLS gold threshold in mg/L"
    )
    
    @model_validator(mode='after')
    def validate_min_max_pairs(self):
        if self.application_rate_min_L_m2_hr >= self.application_rate_max_L_m2_hr:
            raise ValueError("application_rate_min must be less than application_rate_max")
        if self.cn_min_ppm >= self.cn_max_ppm:
            raise ValueError("cn_min must be less than cn_max")
        if self.ph_min >= self.ph_max:
            raise ValueError("ph_min must be less than ph_max")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "application_rate_min_L_m2_hr": 5.0,
                "application_rate_max_L_m2_hr": 15.0,
                "cn_min_ppm": 100.0,
                "cn_max_ppm": 500.0,
                "ph_min": 10.5,
                "ph_max": 11.5,
                "pls_return_min_pct": 70.0,
                "pond_freeboard_min_m": 0.5,
                "cn_consumption_max_kgpt": 0.5,
                "cn_efficiency_min_gpkg": 2.0,
                "pls_low_au_mgL": 0.1
            }
        }


class BenchmarkConfigUpdate(BaseModel):
    """Request schema for updating a BenchmarkConfig."""
    
    application_rate_min_L_m2_hr: Optional[float] = Field(default=None, gt=0)
    application_rate_max_L_m2_hr: Optional[float] = Field(default=None, gt=0)
    cn_min_ppm: Optional[float] = Field(default=None, ge=0)
    cn_max_ppm: Optional[float] = Field(default=None, gt=0)
    ph_min: Optional[float] = Field(default=None, ge=10.0)
    ph_max: Optional[float] = Field(default=None, gt=10.0)
    pls_return_min_pct: Optional[float] = Field(default=None, ge=0, le=100)
    pond_freeboard_min_m: Optional[float] = Field(default=None, gt=0)
    cn_consumption_max_kgpt: Optional[float] = Field(default=None, gt=0)
    cn_efficiency_min_gpkg: Optional[float] = Field(default=None, gt=0)
    pls_low_au_mgL: Optional[float] = Field(default=None, ge=0)
    change_reason: str = Field(
        ...,
        min_length=1,
        description="Reason for the benchmark change (required)"
    )


class BenchmarkConfigResponse(BaseModel):
    """Response schema for BenchmarkConfig."""
    
    id: str
    heap_config_id: str
    application_rate_min_L_m2_hr: float
    application_rate_max_L_m2_hr: float
    cn_min_ppm: float
    cn_max_ppm: float
    ph_min: float
    ph_max: float
    pls_return_min_pct: float
    pond_freeboard_min_m: float
    cn_consumption_max_kgpt: float
    cn_efficiency_min_gpkg: float
    pls_low_au_mgL: float
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    class Config:
        from_attributes = True


class BenchmarkChangeLogResponse(BaseModel):
    """Response schema for BenchmarkChangeLog."""
    
    id: str
    benchmark_config_id: str
    field_name: str
    previous_value: Optional[float]
    new_value: float
    changed_at: datetime
    changed_by: str
    change_reason: str
    
    class Config:
        from_attributes = True


class DailyControlLogCreate(BaseModel):
    """
    Request schema for creating a DailyControlLog.
    
    All fields are required. Records are immutable after submission.
    Only Contractor role may create new records.
    """
    
    log_date: date = Field(
        ...,
        description="Date of the control log entry"
    )
    area_irrigated_m2: float = Field(
        ...,
        ge=0,
        description="Area irrigated in square meters (must be >= 0)"
    )
    flow_m3_per_hr: float = Field(
        ...,
        ge=0,
        description="Flow rate in cubic meters per hour (must be >= 0)"
    )
    irrigation_hours: float = Field(
        ...,
        ge=0,
        le=24,
        description="Irrigation hours (must be >= 0 and <= 24)"
    )
    applied_cn_ppm: float = Field(
        ...,
        ge=0,
        description="Applied cyanide concentration in ppm (must be >= 0)"
    )
    applied_ph: float = Field(
        ...,
        ge=0,
        le=14,
        description="Applied pH (must be between 0 and 14)"
    )
    pls_flow_m3: float = Field(
        ...,
        ge=0,
        description="PLS flow in cubic meters (must be >= 0)"
    )
    pls_au_mgL: float = Field(
        ...,
        ge=0,
        description="PLS gold concentration in mg/L (must be >= 0)"
    )
    pond_freeboard_m: float = Field(
        ...,
        ge=0,
        description="Pond freeboard in meters (must be >= 0)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "log_date": "2024-12-17",
                "area_irrigated_m2": 500.0,
                "flow_m3_per_hr": 25.0,
                "irrigation_hours": 20.0,
                "applied_cn_ppm": 250.0,
                "applied_ph": 10.8,
                "pls_flow_m3": 480.0,
                "pls_au_mgL": 0.85,
                "pond_freeboard_m": 0.75
            }
        }


class DailyControlLogResponse(BaseModel):
    """
    Response schema for DailyControlLog.
    
    Records are immutable - no update or delete operations available.
    """
    
    id: str
    heap_config_id: str
    log_date: date
    area_irrigated_m2: float
    flow_m3_per_hr: float
    irrigation_hours: float
    applied_cn_ppm: float
    applied_ph: float
    pls_flow_m3: float
    pls_au_mgL: float
    pond_freeboard_m: float
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class DailyControlLogWithAlertsResponse(BaseModel):
    """
    Response schema for DailyControlLog with any triggered soft alerts.
    
    Returned after successful submission to show the log and any alerts generated.
    """
    
    daily_control_log: DailyControlLogResponse
    alerts: List["ControlRuleLogResponse"] = Field(
        default=[],
        description="List of soft alerts triggered by this submission"
    )
    calculated_values: dict = Field(
        default={},
        description="Calculated values used for rule evaluation"
    )


class ControlRuleLogResponse(BaseModel):
    """
    Response schema for ControlRuleLog.
    
    Records are immutable - logs all triggered control rules.
    """
    
    id: str
    heap_config_id: str
    daily_control_log_id: Optional[str]
    rule_id: str
    rule_type: str
    rule_message: str
    triggering_field: str
    triggering_value: float
    benchmark_field: Optional[str]
    benchmark_value: Optional[float]
    log_date: date
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class HardStopError(BaseModel):
    """
    Response schema for hard stop errors.
    
    Returned when a hard stop rule is triggered and submission is blocked.
    """
    
    rule_id: str = Field(..., description="Rule identifier (e.g., HS-1, HS-2)")
    rule_type: str = Field(default="HARD_STOP", description="Always HARD_STOP")
    message: str = Field(..., description="Human-readable error message")
    triggering_field: str = Field(..., description="Field that triggered the rule")
    triggering_value: float = Field(..., description="Value that triggered the rule")
    benchmark_field: str = Field(..., description="Benchmark field used for comparison")
    benchmark_value: float = Field(..., description="Benchmark value used for comparison")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rule_id": "HS-1",
                "rule_type": "HARD_STOP",
                "message": "Unsafe pH level – cyanide stability risk. Correct before leaching.",
                "triggering_field": "applied_ph",
                "triggering_value": 9.5,
                "benchmark_field": "ph_min",
                "benchmark_value": 10.5
            }
        }


class WeeklyControlSummaryCreate(BaseModel):
    """
    Request schema for creating a WeeklyControlSummary.
    
    Only cn_used_kg is provided by the user. All other fields are
    system-generated from DailyControlLog aggregation.
    """
    
    week_start_date: date = Field(
        ...,
        description="Start date of the week (Monday-based ISO week)"
    )
    week_end_date: date = Field(
        ...,
        description="End date of the week (Sunday)"
    )
    cn_used_kg: float = Field(
        ...,
        ge=0,
        description="Total NaCN used during the week in kg (must be >= 0)"
    )
    
    @model_validator(mode='after')
    def validate_week_dates(self):
        if self.week_end_date < self.week_start_date:
            raise ValueError("week_end_date must be >= week_start_date")
        days_diff = (self.week_end_date - self.week_start_date).days
        if days_diff != 6:
            raise ValueError("Week must be exactly 7 days (week_end_date - week_start_date = 6 days)")
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "week_start_date": "2024-12-16",
                "week_end_date": "2024-12-22",
                "cn_used_kg": 150.0
            }
        }


class WeeklyControlSummaryResponse(BaseModel):
    """
    Response schema for WeeklyControlSummary.
    
    Includes all aggregated and calculated fields.
    """
    
    id: str
    heap_config_id: str
    week_start_date: date
    week_end_date: date
    cn_used_kg: float
    weekly_solution_applied_m3: float
    weekly_pls_flow_m3: float
    weekly_gold_in_pls_g: float
    cumulative_gold_in_pls_g: float
    contained_gold_g: Optional[float]
    recovery_pct: Optional[float]
    cn_consumption_kgpt: Optional[float]
    cn_efficiency_gpkg: Optional[float]
    is_approved: int
    approved_at: Optional[datetime]
    approved_by: Optional[str]
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class WeeklyControlSummaryWithAlertsResponse(BaseModel):
    """
    Response schema for WeeklyControlSummary with any triggered weekly flags.
    
    Returned after successful creation to show the summary and any alerts generated.
    """
    
    weekly_summary: WeeklyControlSummaryResponse
    alerts: List["ControlRuleLogResponse"] = Field(
        default=[],
        description="List of weekly flags triggered by this summary"
    )
    aggregation_details: dict = Field(
        default={},
        description="Details about the aggregation (days included, any errors)"
    )


class HeapLeachingConfig(BaseModel):
    """
    Configuration schema for Heap Leaching – Key Controls module.
    
    This configuration defines the operational parameters for a single
    heap leaching instance. All fields have sensible defaults based on
    the engineering assumptions, but can be edited as needed.
    
    Note: This is a configuration placeholder. Data models and operational
    data processing will be added in future iterations.
    """
    
    heap_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the heap instance (auto-generated if not provided)"
    )
    
    heap_name: Optional[str] = Field(
        default=None,
        description="Human-readable name for the heap"
    )
    
    heap_leaching_start_date: Optional[date] = Field(
        default=None,
        description="Start date for heap leaching operations (required before operational data)"
    )
    
    target_heap_size_tonnes: float = Field(
        default=1000.0,
        ge=0,
        description="Target heap size in tonnes (default: 1000)"
    )
    
    ore_type: OreType = Field(
        default=OreType.OXIDE_GOLD,
        description="Type of ore being processed (default: oxide gold)"
    )
    
    recovery_method: RecoveryMethod = Field(
        default=RecoveryMethod.SOLUTION_BASED_PLS,
        description="Recovery method used (default: solution-based PLS reporting)"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "heap_id": "HEAP-20241217-ABC12",
                "heap_name": "Heap Pad 1",
                "heap_leaching_start_date": "2024-12-17",
                "target_heap_size_tonnes": 1000.0,
                "ore_type": "oxide_gold",
                "recovery_method": "solution_based_pls"
            }
        }


class HeapLeachingConfigResponse(BaseModel):
    """Response model for configuration retrieval."""
    
    module_id: str = Field(
        default="heap_leaching_key_controls",
        description="Module identifier"
    )
    
    module_name: str = Field(
        default="Heap Leaching – Key Controls",
        description="Module display name"
    )
    
    config: Optional[HeapLeachingConfig] = Field(
        default=None,
        description="Current configuration (None if not yet configured)"
    )
    
    is_configured: bool = Field(
        default=False,
        description="Whether the module has been configured"
    )
    
    has_operational_data: bool = Field(
        default=False,
        description="Whether operational data exists (always False in this version)"
    )
    
    message: str = Field(
        default="Module registered. Configuration accepted but no operational data processing available yet.",
        description="Status message"
    )
