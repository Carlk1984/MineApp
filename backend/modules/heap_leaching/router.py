"""
Heap Leaching – Key Controls API Router

Provides API endpoints for HeapConfig and BenchmarkConfig management
with role-based access control and change logging.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, date

from database import get_db
from auth import (
    get_current_active_user,
    require_admin,
    require_manager_or_above,
    require_contractor,
    require_engineer_or_above,
)
import models as user_models

from modules.heap_leaching.metadata import MODULE_METADATA, get_module_summary
from modules.heap_leaching.config import (
    HeapLeachingConfig,
    HeapLeachingConfigResponse,
    HeapConfigCreate,
    HeapConfigUpdate,
    HeapConfigResponse,
    BenchmarkConfigCreate,
    BenchmarkConfigUpdate,
    BenchmarkConfigResponse,
    BenchmarkChangeLogResponse,
    DailyControlLogCreate,
    DailyControlLogResponse,
)
from modules.heap_leaching.models import (
    HeapConfig,
    HeapConfigHistory,
    BenchmarkConfig,
    BenchmarkChangeLog,
    DailyControlLog,
)

router = APIRouter(
    prefix="/heap-leaching",
    tags=["Heap Leaching – Key Controls"],
)


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
    "/status",
    response_model=Dict[str, Any],
    summary="Get module status",
    description="Returns the current status of the module including configuration state.",
)
async def get_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return the current status of the module."""
    heap_config = db.query(HeapConfig).first()
    benchmark_config = None
    if heap_config:
        benchmark_config = db.query(BenchmarkConfig).filter(
            BenchmarkConfig.heap_config_id == heap_config.id
        ).first()
    
    return {
        "module_id": MODULE_METADATA["module_id"],
        "module_name": MODULE_METADATA["name"],
        "version": MODULE_METADATA["version"],
        "status": MODULE_METADATA["status"],
        "heap_config_exists": heap_config is not None,
        "benchmark_config_exists": benchmark_config is not None,
        "ready_for_operational_data": heap_config is not None and benchmark_config is not None,
        "data_models_defined": True,
        "message": (
            "Module ready for operational data entry."
            if heap_config and benchmark_config
            else "Module registered. HeapConfig and BenchmarkConfig required before operational data."
        ),
    }


@router.post(
    "/heap-config",
    response_model=HeapConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create heap configuration",
    description="Creates a new heap configuration. Requires Admin or Manager role.",
)
async def create_heap_config(
    config: HeapConfigCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_manager_or_above),
) -> HeapConfigResponse:
    """
    Create a new heap configuration.
    
    Only one HeapConfig per module instance is allowed.
    Requires Admin or Manager role.
    """
    existing = db.query(HeapConfig).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HeapConfig already exists. Use PUT to update."
        )
    
    existing_heap_id = db.query(HeapConfig).filter(HeapConfig.heap_id == config.heap_id).first()
    if existing_heap_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Heap ID '{config.heap_id}' already exists."
        )
    
    db_config = HeapConfig(
        heap_id=config.heap_id,
        heap_tonnage_t=config.heap_tonnage_t,
        head_grade_gpt=config.head_grade_gpt,
        leach_start_date=config.leach_start_date,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return HeapConfigResponse.model_validate(db_config)


@router.get(
    "/heap-config",
    response_model=HeapConfigResponse,
    summary="Get heap configuration",
    description="Returns the current heap configuration.",
)
async def get_heap_config(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
) -> HeapConfigResponse:
    """Get the current heap configuration."""
    config = db.query(HeapConfig).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. Create one first."
        )
    return HeapConfigResponse.model_validate(config)


@router.put(
    "/heap-config",
    response_model=HeapConfigResponse,
    summary="Update heap configuration",
    description="Updates the heap configuration. Requires Admin or Manager role. Changes are versioned.",
)
async def update_heap_config(
    config: HeapConfigUpdate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_manager_or_above),
) -> HeapConfigResponse:
    """
    Update the heap configuration.
    
    Requires Admin or Manager role.
    Changes are versioned and timestamped.
    """
    db_config = db.query(HeapConfig).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. Create one first."
        )
    
    history = HeapConfigHistory(
        heap_config_id=db_config.id,
        heap_id=db_config.heap_id,
        heap_tonnage_t=db_config.heap_tonnage_t,
        head_grade_gpt=db_config.head_grade_gpt,
        leach_start_date=db_config.leach_start_date,
        version=db_config.version,
        changed_by=current_user.id,
        change_reason=config.change_reason,
    )
    db.add(history)
    
    if config.heap_tonnage_t is not None:
        db_config.heap_tonnage_t = config.heap_tonnage_t
    if config.head_grade_gpt is not None:
        db_config.head_grade_gpt = config.head_grade_gpt
    if config.leach_start_date is not None:
        db_config.leach_start_date = config.leach_start_date
    
    db_config.version += 1
    db_config.updated_by = current_user.id
    db_config.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_config)
    
    return HeapConfigResponse.model_validate(db_config)


@router.get(
    "/heap-config/history",
    response_model=List[Dict[str, Any]],
    summary="Get heap configuration history",
    description="Returns the version history of the heap configuration.",
)
async def get_heap_config_history(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_manager_or_above),
) -> List[Dict[str, Any]]:
    """Get the version history of the heap configuration."""
    history = db.query(HeapConfigHistory).order_by(HeapConfigHistory.changed_at.desc()).all()
    return [
        {
            "id": h.id,
            "heap_config_id": h.heap_config_id,
            "heap_id": h.heap_id,
            "heap_tonnage_t": h.heap_tonnage_t,
            "head_grade_gpt": h.head_grade_gpt,
            "leach_start_date": h.leach_start_date.isoformat() if h.leach_start_date else None,
            "version": h.version,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
            "changed_by": h.changed_by,
            "change_reason": h.change_reason,
        }
        for h in history
    ]


@router.post(
    "/benchmark-config",
    response_model=BenchmarkConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create benchmark configuration",
    description="Creates benchmark configuration. Requires Admin role. HeapConfig must exist first.",
)
async def create_benchmark_config(
    config: BenchmarkConfigCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_admin),
) -> BenchmarkConfigResponse:
    """
    Create benchmark configuration.
    
    Requires Admin role.
    HeapConfig must exist before creating BenchmarkConfig.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HeapConfig must exist before creating BenchmarkConfig."
        )
    
    existing = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BenchmarkConfig already exists for this heap. Use PUT to update."
        )
    
    db_config = BenchmarkConfig(
        heap_config_id=heap_config.id,
        application_rate_min_L_m2_hr=config.application_rate_min_L_m2_hr,
        application_rate_max_L_m2_hr=config.application_rate_max_L_m2_hr,
        cn_min_ppm=config.cn_min_ppm,
        cn_max_ppm=config.cn_max_ppm,
        ph_min=config.ph_min,
        ph_max=config.ph_max,
        pls_return_min_pct=config.pls_return_min_pct,
        pond_freeboard_min_m=config.pond_freeboard_min_m,
        cn_consumption_max_kgpt=config.cn_consumption_max_kgpt,
        cn_efficiency_min_gpkg=config.cn_efficiency_min_gpkg,
        pls_low_au_mgL=config.pls_low_au_mgL,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return BenchmarkConfigResponse.model_validate(db_config)


@router.get(
    "/benchmark-config",
    response_model=BenchmarkConfigResponse,
    summary="Get benchmark configuration",
    description="Returns the current benchmark configuration.",
)
async def get_benchmark_config(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
) -> BenchmarkConfigResponse:
    """Get the current benchmark configuration."""
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. Create HeapConfig first."
        )
    
    config = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BenchmarkConfig not found. Create one first."
        )
    return BenchmarkConfigResponse.model_validate(config)


@router.put(
    "/benchmark-config",
    response_model=BenchmarkConfigResponse,
    summary="Update benchmark configuration",
    description="Updates benchmark configuration. Requires Admin role. All changes are logged.",
)
async def update_benchmark_config(
    config: BenchmarkConfigUpdate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_admin),
) -> BenchmarkConfigResponse:
    """
    Update benchmark configuration.
    
    Requires Admin role.
    All changes are logged with previous value, new value, user, timestamp, and reason.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found."
        )
    
    db_config = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BenchmarkConfig not found. Create one first."
        )
    
    benchmark_fields = [
        "application_rate_min_L_m2_hr",
        "application_rate_max_L_m2_hr",
        "cn_min_ppm",
        "cn_max_ppm",
        "ph_min",
        "ph_max",
        "pls_return_min_pct",
        "pond_freeboard_min_m",
        "cn_consumption_max_kgpt",
        "cn_efficiency_min_gpkg",
        "pls_low_au_mgL",
    ]
    
    for field in benchmark_fields:
        new_value = getattr(config, field, None)
        if new_value is not None:
            old_value = getattr(db_config, field)
            if old_value != new_value:
                change_log = BenchmarkChangeLog(
                    benchmark_config_id=db_config.id,
                    field_name=field,
                    previous_value=old_value,
                    new_value=new_value,
                    changed_by=current_user.id,
                    change_reason=config.change_reason,
                )
                db.add(change_log)
                setattr(db_config, field, new_value)
    
    db_config.version += 1
    db_config.updated_by = current_user.id
    db_config.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_config)
    
    return BenchmarkConfigResponse.model_validate(db_config)


@router.get(
    "/benchmark-config/change-log",
    response_model=List[BenchmarkChangeLogResponse],
    summary="Get benchmark change log",
    description="Returns the change log for all benchmark configuration changes.",
)
async def get_benchmark_change_log(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_admin),
) -> List[BenchmarkChangeLogResponse]:
    """Get the change log for benchmark configuration."""
    logs = db.query(BenchmarkChangeLog).order_by(BenchmarkChangeLog.changed_at.desc()).all()
    return [BenchmarkChangeLogResponse.model_validate(log) for log in logs]


@router.post(
    "/daily-control-log",
    response_model=DailyControlLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create daily control log",
    description="Creates a new daily control log entry. Requires Contractor role. Records are immutable after submission.",
)
async def create_daily_control_log(
    log_data: DailyControlLogCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_contractor),
) -> DailyControlLogResponse:
    """
    Create a new daily control log entry.
    
    Requirements:
    - Requires Contractor role
    - HeapConfig and BenchmarkConfig must exist before creating logs
    - One log per calendar day per heap
    - Records are IMMUTABLE after submission (no edits or deletions)
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HeapConfig must exist before creating daily control logs."
        )
    
    benchmark_config = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    if not benchmark_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BenchmarkConfig must exist before creating daily control logs."
        )
    
    existing_log = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config.id,
        DailyControlLog.log_date == log_data.log_date,
    ).first()
    if existing_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A daily control log already exists for {log_data.log_date}. Records are immutable."
        )
    
    db_log = DailyControlLog(
        heap_config_id=heap_config.id,
        log_date=log_data.log_date,
        area_irrigated_m2=log_data.area_irrigated_m2,
        flow_m3_per_hr=log_data.flow_m3_per_hr,
        irrigation_hours=log_data.irrigation_hours,
        applied_cn_ppm=log_data.applied_cn_ppm,
        applied_ph=log_data.applied_ph,
        pls_flow_m3=log_data.pls_flow_m3,
        pls_au_mgL=log_data.pls_au_mgL,
        pond_freeboard_m=log_data.pond_freeboard_m,
        created_by=current_user.id,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return DailyControlLogResponse.model_validate(db_log)


@router.get(
    "/daily-control-log",
    response_model=List[DailyControlLogResponse],
    summary="List daily control logs",
    description="Returns all daily control logs. All authenticated users can read logs.",
)
async def list_daily_control_logs(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
    start_date: Optional[date] = Query(default=None, description="Filter logs from this date"),
    end_date: Optional[date] = Query(default=None, description="Filter logs until this date"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(default=0, ge=0, description="Number of logs to skip"),
) -> List[DailyControlLogResponse]:
    """
    List daily control logs with optional date filtering.
    
    All authenticated users (Contractor, Engineer, Manager, Admin) can read logs.
    Records are immutable - no update or delete operations available.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. No logs available."
        )
    
    query = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config.id
    )
    
    if start_date:
        query = query.filter(DailyControlLog.log_date >= start_date)
    if end_date:
        query = query.filter(DailyControlLog.log_date <= end_date)
    
    logs = query.order_by(DailyControlLog.log_date.desc()).offset(offset).limit(limit).all()
    return [DailyControlLogResponse.model_validate(log) for log in logs]


@router.get(
    "/daily-control-log/{log_date}",
    response_model=DailyControlLogResponse,
    summary="Get daily control log by date",
    description="Returns the daily control log for a specific date. All authenticated users can read logs.",
)
async def get_daily_control_log(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
) -> DailyControlLogResponse:
    """
    Get the daily control log for a specific date.
    
    All authenticated users (Contractor, Engineer, Manager, Admin) can read logs.
    Records are immutable - no update or delete operations available.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found."
        )
    
    log = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config.id,
        DailyControlLog.log_date == log_date,
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No daily control log found for {log_date}."
        )
    
    return DailyControlLogResponse.model_validate(log)
