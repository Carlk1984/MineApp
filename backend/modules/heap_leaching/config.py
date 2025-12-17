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
