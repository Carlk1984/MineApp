"""
Heap Leaching – Key Controls Configuration Schema

Defines the configuration input structure for the module.
This module accepts configuration input but has no operational data yet.

Note: Data models will be defined in a future iteration.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from enum import Enum


class OreType(str, Enum):
    """Supported ore types for heap leaching."""
    OXIDE_GOLD = "oxide_gold"


class RecoveryMethod(str, Enum):
    """Supported recovery methods."""
    SOLUTION_BASED_PLS = "solution_based_pls"


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
