"""
Heap Leaching – Key Controls API Router

Provides API endpoints for module registration and configuration.
Operational endpoints will be added in future iterations.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional

from modules.heap_leaching.metadata import MODULE_METADATA, get_module_summary
from modules.heap_leaching.config import (
    HeapLeachingConfig,
    HeapLeachingConfigResponse,
)

router = APIRouter(
    prefix="/heap-leaching",
    tags=["Heap Leaching – Key Controls"],
)

_current_config: Optional[HeapLeachingConfig] = None


@router.get(
    "/metadata",
    response_model=Dict[str, Any],
    summary="Get module metadata",
    description="Returns the full metadata for the Heap Leaching – Key Controls module.",
)
async def get_metadata() -> Dict[str, Any]:
    """Return the module metadata including purpose, scope, and constraints."""
    return MODULE_METADATA


@router.get(
    "/summary",
    response_model=Dict[str, Any],
    summary="Get module summary",
    description="Returns a brief summary of the module for registration purposes.",
)
async def get_summary() -> Dict[str, Any]:
    """Return a summary of the module for registration purposes."""
    return get_module_summary()


@router.get(
    "/config",
    response_model=HeapLeachingConfigResponse,
    summary="Get current configuration",
    description="Returns the current configuration for the heap leaching instance.",
)
async def get_config() -> HeapLeachingConfigResponse:
    """Return the current configuration state."""
    global _current_config
    
    return HeapLeachingConfigResponse(
        module_id=MODULE_METADATA["module_id"],
        module_name=MODULE_METADATA["name"],
        config=_current_config,
        is_configured=_current_config is not None,
        has_operational_data=False,
        message=(
            "Configuration set. Awaiting operational data processing implementation."
            if _current_config is not None
            else "Module registered. Configuration accepted but no operational data processing available yet."
        ),
    )


@router.post(
    "/config",
    response_model=HeapLeachingConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set configuration",
    description="Sets the configuration for the heap leaching instance.",
)
async def set_config(config: HeapLeachingConfig) -> HeapLeachingConfigResponse:
    """
    Set the configuration for the heap leaching instance.
    
    Note: This stores the configuration but does not process operational data.
    Operational data processing will be added in future iterations.
    """
    global _current_config
    _current_config = config
    
    return HeapLeachingConfigResponse(
        module_id=MODULE_METADATA["module_id"],
        module_name=MODULE_METADATA["name"],
        config=_current_config,
        is_configured=True,
        has_operational_data=False,
        message="Configuration set. Awaiting operational data processing implementation.",
    )


@router.put(
    "/config",
    response_model=HeapLeachingConfigResponse,
    summary="Update configuration",
    description="Updates the configuration for the heap leaching instance.",
)
async def update_config(config: HeapLeachingConfig) -> HeapLeachingConfigResponse:
    """
    Update the configuration for the heap leaching instance.
    
    Note: This updates the configuration but does not process operational data.
    """
    global _current_config
    _current_config = config
    
    return HeapLeachingConfigResponse(
        module_id=MODULE_METADATA["module_id"],
        module_name=MODULE_METADATA["name"],
        config=_current_config,
        is_configured=True,
        has_operational_data=False,
        message="Configuration updated. Awaiting operational data processing implementation.",
    )


@router.delete(
    "/config",
    response_model=Dict[str, str],
    summary="Clear configuration",
    description="Clears the current configuration for the heap leaching instance.",
)
async def clear_config() -> Dict[str, str]:
    """Clear the current configuration."""
    global _current_config
    _current_config = None
    
    return {
        "status": "cleared",
        "message": "Configuration cleared. Module remains registered.",
    }


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Get module status",
    description="Returns the current status of the module.",
)
async def get_status() -> Dict[str, Any]:
    """Return the current status of the module."""
    global _current_config
    
    return {
        "module_id": MODULE_METADATA["module_id"],
        "module_name": MODULE_METADATA["name"],
        "version": MODULE_METADATA["version"],
        "status": MODULE_METADATA["status"],
        "is_configured": _current_config is not None,
        "has_operational_data": False,
        "data_models_defined": False,
        "message": (
            "Module registered and configured. Awaiting data models and operational processing."
            if _current_config is not None
            else "Module registered. Awaiting configuration input."
        ),
    }
