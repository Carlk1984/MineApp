"""
Heap Leaching – Key Controls API Router

Provides API endpoints for HeapConfig and BenchmarkConfig management
with role-based access control and change logging.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, date
import csv
import io
import json

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
from sqlalchemy import func

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
    DailyControlLogWithAlertsResponse,
    ControlRuleLogResponse,
    HardStopError,
    WeeklyControlSummaryCreate,
    WeeklyControlSummaryResponse,
    WeeklyControlSummaryWithAlertsResponse,
    StopLeachDecisionResponse,
    StopLeachDecisionWithOverrideResponse,
    StopLeachOverrideCreate,
    StopLeachOverrideResponse,
)
from modules.heap_leaching.models import (
    HeapConfig,
    HeapConfigHistory,
    BenchmarkConfig,
    BenchmarkChangeLog,
    DailyControlLog,
    ControlRuleLog,
    WeeklyControlSummary,
    StopLeachDecision,
    StopLeachOverride,
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


def calculate_application_rate(flow_m3_per_hr: float, area_irrigated_m2: float) -> float:
    """
    Calculate application rate in L/m²/hr.
    
    Formula: (flow_m3_per_hr * 1000) / area_irrigated_m2
    Returns 0 if area is 0 to avoid division by zero.
    """
    if area_irrigated_m2 <= 0:
        return 0.0
    return (flow_m3_per_hr * 1000) / area_irrigated_m2


def calculate_pls_return_pct(pls_flow_m3: float, flow_m3_per_hr: float, irrigation_hours: float) -> float:
    """
    Calculate PLS return percentage.
    
    Formula: (pls_flow_m3 / (flow_m3_per_hr * irrigation_hours)) * 100
    Returns 0 if applied volume is 0 to avoid division by zero.
    """
    applied_volume = flow_m3_per_hr * irrigation_hours
    if applied_volume <= 0:
        return 0.0
    return (pls_flow_m3 / applied_volume) * 100


def evaluate_hard_stops(
    log_data: DailyControlLogCreate,
    benchmark_config: BenchmarkConfig,
) -> List[Dict[str, Any]]:
    """
    Evaluate hard stop rules that block submission.
    
    Returns a list of triggered hard stop rules.
    """
    hard_stops = []
    
    # HS-1: Unsafe pH
    if log_data.applied_ph < benchmark_config.ph_min:
        hard_stops.append({
            "rule_id": "HS-1",
            "rule_type": "HARD_STOP",
            "message": "Unsafe pH level – cyanide stability risk. Correct before leaching.",
            "triggering_field": "applied_ph",
            "triggering_value": log_data.applied_ph,
            "benchmark_field": "ph_min",
            "benchmark_value": benchmark_config.ph_min,
        })
    
    # HS-2: Insufficient Pond Freeboard
    if log_data.pond_freeboard_m < benchmark_config.pond_freeboard_min_m:
        hard_stops.append({
            "rule_id": "HS-2",
            "rule_type": "HARD_STOP",
            "message": "Pond freeboard below minimum – stop irrigation immediately.",
            "triggering_field": "pond_freeboard_m",
            "triggering_value": log_data.pond_freeboard_m,
            "benchmark_field": "pond_freeboard_min_m",
            "benchmark_value": benchmark_config.pond_freeboard_min_m,
        })
    
    return hard_stops


def evaluate_soft_alerts(
    log_data: DailyControlLogCreate,
    benchmark_config: BenchmarkConfig,
    application_rate: float,
    pls_return_pct: float,
) -> List[Dict[str, Any]]:
    """
    Evaluate soft alert rules that flag issues but allow submission.
    
    Returns a list of triggered soft alert rules.
    """
    soft_alerts = []
    
    # SA-1: Application Rate Non-Compliance
    if application_rate < benchmark_config.application_rate_min_L_m2_hr or \
       application_rate > benchmark_config.application_rate_max_L_m2_hr:
        soft_alerts.append({
            "rule_id": "SA-1",
            "rule_type": "SOFT_ALERT",
            "message": "Solution application rate outside benchmark.",
            "triggering_field": "application_rate_L_m2_hr",
            "triggering_value": application_rate,
            "benchmark_field": "application_rate_min/max_L_m2_hr",
            "benchmark_value": f"{benchmark_config.application_rate_min_L_m2_hr}-{benchmark_config.application_rate_max_L_m2_hr}",
        })
    
    # SA-2: Cyanide Strength Non-Compliance
    if log_data.applied_cn_ppm < benchmark_config.cn_min_ppm or \
       log_data.applied_cn_ppm > benchmark_config.cn_max_ppm:
        soft_alerts.append({
            "rule_id": "SA-2",
            "rule_type": "SOFT_ALERT",
            "message": "Applied cyanide concentration outside benchmark.",
            "triggering_field": "applied_cn_ppm",
            "triggering_value": log_data.applied_cn_ppm,
            "benchmark_field": "cn_min/max_ppm",
            "benchmark_value": f"{benchmark_config.cn_min_ppm}-{benchmark_config.cn_max_ppm}",
        })
    
    # SA-3: Poor Heap Permeability
    if pls_return_pct < benchmark_config.pls_return_min_pct:
        soft_alerts.append({
            "rule_id": "SA-3",
            "rule_type": "SOFT_ALERT",
            "message": "Low PLS return – possible permeability or channeling issue.",
            "triggering_field": "pls_return_pct",
            "triggering_value": pls_return_pct,
            "benchmark_field": "pls_return_min_pct",
            "benchmark_value": benchmark_config.pls_return_min_pct,
        })
    
    # SA-4: No Gold Reporting
    if log_data.pls_au_mgL == 0:
        soft_alerts.append({
            "rule_id": "SA-4",
            "rule_type": "SOFT_ALERT",
            "message": "No gold detected in PLS.",
            "triggering_field": "pls_au_mgL",
            "triggering_value": log_data.pls_au_mgL,
            "benchmark_field": None,
            "benchmark_value": None,
        })
    
    return soft_alerts


@router.post(
    "/daily-control-log",
    response_model=DailyControlLogWithAlertsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create daily control log",
    description="Creates a new daily control log entry. Requires Contractor role. Evaluates control rules (hard stops block submission, soft alerts are logged). Records are immutable after submission.",
)
async def create_daily_control_log(
    log_data: DailyControlLogCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_contractor),
) -> DailyControlLogWithAlertsResponse:
    """
    Create a new daily control log entry with control rule evaluation.
    
    Requirements:
    - Requires Contractor role
    - HeapConfig and BenchmarkConfig must exist before creating logs
    - One log per calendar day per heap
    - Records are IMMUTABLE after submission (no edits or deletions)
    
    Control Rules:
    - Hard Stops (HS-1, HS-2): Block submission if triggered
    - Soft Alerts (SA-1 to SA-4): Log and flag but allow submission
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
    
    # Calculate derived values for rule evaluation
    application_rate = calculate_application_rate(
        log_data.flow_m3_per_hr, log_data.area_irrigated_m2
    )
    pls_return_pct = calculate_pls_return_pct(
        log_data.pls_flow_m3, log_data.flow_m3_per_hr, log_data.irrigation_hours
    )
    
    calculated_values = {
        "application_rate_L_m2_hr": round(application_rate, 4),
        "pls_return_pct": round(pls_return_pct, 2),
    }
    
    # Evaluate hard stop rules first
    hard_stops = evaluate_hard_stops(log_data, benchmark_config)
    
    if hard_stops:
        # Log hard stops before blocking
        for hs in hard_stops:
            hard_stop_log = ControlRuleLog(
                heap_config_id=heap_config.id,
                daily_control_log_id=None,  # No log created due to hard stop
                rule_id=hs["rule_id"],
                rule_type=hs["rule_type"],
                rule_message=hs["message"],
                triggering_field=hs["triggering_field"],
                triggering_value=hs["triggering_value"],
                benchmark_field=hs["benchmark_field"],
                benchmark_value=hs["benchmark_value"],
                log_date=log_data.log_date,
                created_by=current_user.id,
            )
            db.add(hard_stop_log)
        db.commit()
        
        # Return error with all hard stops
        error_detail = {
            "hard_stops": hard_stops,
            "message": "Submission blocked due to hard stop rule(s). See hard_stops for details.",
            "calculated_values": calculated_values,
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail,
        )
    
    # Create the daily control log
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
    db.flush()  # Get the ID without committing
    
    # Evaluate soft alert rules
    soft_alerts = evaluate_soft_alerts(
        log_data, benchmark_config, application_rate, pls_return_pct
    )
    
    # Log soft alerts
    alert_logs = []
    for sa in soft_alerts:
        # Handle benchmark_value that might be a string (for ranges)
        benchmark_val = sa["benchmark_value"]
        if isinstance(benchmark_val, str):
            # For range values, store the min value
            benchmark_val = None
        
        alert_log = ControlRuleLog(
            heap_config_id=heap_config.id,
            daily_control_log_id=db_log.id,
            rule_id=sa["rule_id"],
            rule_type=sa["rule_type"],
            rule_message=sa["message"],
            triggering_field=sa["triggering_field"],
            triggering_value=sa["triggering_value"],
            benchmark_field=sa["benchmark_field"],
            benchmark_value=benchmark_val,
            log_date=log_data.log_date,
            created_by=current_user.id,
        )
        db.add(alert_log)
        alert_logs.append(alert_log)
    
    db.commit()
    db.refresh(db_log)
    
    # Refresh alert logs to get IDs
    for alert_log in alert_logs:
        db.refresh(alert_log)
    
    return DailyControlLogWithAlertsResponse(
        daily_control_log=DailyControlLogResponse.model_validate(db_log),
        alerts=[ControlRuleLogResponse.model_validate(log) for log in alert_logs],
        calculated_values=calculated_values,
    )


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


@router.get(
    "/control-rule-logs",
    response_model=List[ControlRuleLogResponse],
    summary="List control rule logs",
    description="Returns all control rule logs (hard stops and soft alerts). All authenticated users can read logs.",
)
async def list_control_rule_logs(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
    rule_type: Optional[str] = Query(default=None, description="Filter by rule type: HARD_STOP or SOFT_ALERT"),
    rule_id: Optional[str] = Query(default=None, description="Filter by rule ID (e.g., HS-1, SA-1)"),
    start_date: Optional[date] = Query(default=None, description="Filter logs from this date"),
    end_date: Optional[date] = Query(default=None, description="Filter logs until this date"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(default=0, ge=0, description="Number of logs to skip"),
) -> List[ControlRuleLogResponse]:
    """
    List control rule logs with optional filtering.
    
    All authenticated users can read control rule logs.
    Logs are immutable - no update or delete operations available.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. No logs available."
        )
    
    query = db.query(ControlRuleLog).filter(
        ControlRuleLog.heap_config_id == heap_config.id
    )
    
    if rule_type:
        query = query.filter(ControlRuleLog.rule_type == rule_type)
    if rule_id:
        query = query.filter(ControlRuleLog.rule_id == rule_id)
    if start_date:
        query = query.filter(ControlRuleLog.log_date >= start_date)
    if end_date:
        query = query.filter(ControlRuleLog.log_date <= end_date)
    
    logs = query.order_by(ControlRuleLog.created_at.desc()).offset(offset).limit(limit).all()
    return [ControlRuleLogResponse.model_validate(log) for log in logs]


@router.get(
    "/control-rule-logs/{log_date}",
    response_model=List[ControlRuleLogResponse],
    summary="Get control rule logs by date",
    description="Returns all control rule logs for a specific date. All authenticated users can read logs.",
)
async def get_control_rule_logs_by_date(
    log_date: date,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
) -> List[ControlRuleLogResponse]:
    """
    Get all control rule logs for a specific date.
    
    All authenticated users can read control rule logs.
    Logs are immutable - no update or delete operations available.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found."
        )
    
    logs = db.query(ControlRuleLog).filter(
        ControlRuleLog.heap_config_id == heap_config.id,
        ControlRuleLog.log_date == log_date,
    ).order_by(ControlRuleLog.created_at.desc()).all()
    
    return [ControlRuleLogResponse.model_validate(log) for log in logs]


def calculate_daily_solution_applied_m3(flow_m3_per_hr: float, irrigation_hours: float) -> float:
    """
    Calculate daily solution applied in m³.
    
    Formula: flow_m3_per_hr * irrigation_hours
    """
    return flow_m3_per_hr * irrigation_hours


def calculate_daily_gold_in_pls_g(pls_flow_m3: float, pls_au_mgL: float) -> float:
    """
    Calculate daily gold in PLS in grams.
    
    Formula: pls_flow_m3 * pls_au_mgL * 1000 (convert m³ to L) / 1000 (convert mg to g)
    Simplified: pls_flow_m3 * pls_au_mgL
    
    Note: pls_flow_m3 is in m³, pls_au_mgL is in mg/L
    1 m³ = 1000 L, so gold_mg = pls_flow_m3 * 1000 * pls_au_mgL
    gold_g = gold_mg / 1000 = pls_flow_m3 * pls_au_mgL
    """
    return pls_flow_m3 * pls_au_mgL


def aggregate_weekly_data(
    db: Session,
    heap_config_id: str,
    week_start_date: date,
    week_end_date: date,
) -> Dict[str, Any]:
    """
    Aggregate daily control log data for a week.
    
    Returns:
    - weekly_solution_applied_m3: SUM of daily solution applied
    - weekly_pls_flow_m3: SUM of daily PLS flow
    - weekly_gold_in_pls_g: SUM of daily gold in PLS
    - days_with_data: Number of days with data in the week
    - errors: List of any errors encountered
    """
    daily_logs = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config_id,
        DailyControlLog.log_date >= week_start_date,
        DailyControlLog.log_date <= week_end_date,
    ).all()
    
    weekly_solution_applied_m3 = 0.0
    weekly_pls_flow_m3 = 0.0
    weekly_gold_in_pls_g = 0.0
    errors = []
    
    for log in daily_logs:
        daily_solution = calculate_daily_solution_applied_m3(
            log.flow_m3_per_hr, log.irrigation_hours
        )
        daily_gold = calculate_daily_gold_in_pls_g(log.pls_flow_m3, log.pls_au_mgL)
        
        weekly_solution_applied_m3 += daily_solution
        weekly_pls_flow_m3 += log.pls_flow_m3
        weekly_gold_in_pls_g += daily_gold
    
    return {
        "weekly_solution_applied_m3": round(weekly_solution_applied_m3, 4),
        "weekly_pls_flow_m3": round(weekly_pls_flow_m3, 4),
        "weekly_gold_in_pls_g": round(weekly_gold_in_pls_g, 6),
        "days_with_data": len(daily_logs),
        "errors": errors,
    }


def calculate_cumulative_gold(
    db: Session,
    heap_config_id: str,
    up_to_week_end: date,
) -> float:
    """
    Calculate cumulative gold in PLS up to and including a specific week.
    
    Sums weekly_gold_in_pls_g from all WeeklyControlSummary records
    up to the specified week end date.
    """
    result = db.query(func.sum(WeeklyControlSummary.weekly_gold_in_pls_g)).filter(
        WeeklyControlSummary.heap_config_id == heap_config_id,
        WeeklyControlSummary.week_end_date <= up_to_week_end,
    ).scalar()
    
    return result or 0.0


def calculate_economic_metrics(
    heap_config: HeapConfig,
    cumulative_gold_in_pls_g: float,
    cn_used_kg: float,
) -> Dict[str, Any]:
    """
    Calculate economic metrics for a weekly summary.
    
    Returns:
    - contained_gold_g: heap_tonnage_t * head_grade_gpt
    - recovery_pct: (cumulative_gold_in_pls_g / contained_gold_g) * 100
    - cn_consumption_kgpt: cn_used_kg / heap_tonnage_t
    - cn_efficiency_gpkg: cumulative_gold_in_pls_g / cn_used_kg
    - errors: List of any errors encountered
    """
    errors = []
    
    contained_gold_g = None
    recovery_pct = None
    cn_consumption_kgpt = None
    cn_efficiency_gpkg = None
    
    if heap_config.head_grade_gpt is None or heap_config.head_grade_gpt == 0:
        errors.append("head_grade_gpt is NULL or 0 - recovery_pct cannot be calculated")
    else:
        contained_gold_g = heap_config.heap_tonnage_t * heap_config.head_grade_gpt
        if contained_gold_g > 0:
            recovery_pct = (cumulative_gold_in_pls_g / contained_gold_g) * 100
    
    if heap_config.heap_tonnage_t > 0:
        cn_consumption_kgpt = cn_used_kg / heap_config.heap_tonnage_t
    
    if cn_used_kg is None or cn_used_kg == 0:
        errors.append("cn_used_kg is NULL or 0 - cn_efficiency_gpkg cannot be calculated")
    else:
        cn_efficiency_gpkg = cumulative_gold_in_pls_g / cn_used_kg
    
    return {
        "contained_gold_g": round(contained_gold_g, 4) if contained_gold_g is not None else None,
        "recovery_pct": round(recovery_pct, 4) if recovery_pct is not None else None,
        "cn_consumption_kgpt": round(cn_consumption_kgpt, 6) if cn_consumption_kgpt is not None else None,
        "cn_efficiency_gpkg": round(cn_efficiency_gpkg, 6) if cn_efficiency_gpkg is not None else None,
        "errors": errors,
    }


def evaluate_weekly_flags(
    cn_consumption_kgpt: Optional[float],
    cn_efficiency_gpkg: Optional[float],
    benchmark_config: BenchmarkConfig,
) -> List[Dict[str, Any]]:
    """
    Evaluate weekly economic flag rules (soft alerts).
    
    Returns a list of triggered weekly flags.
    """
    weekly_flags = []
    
    # WF-1: Excessive Cyanide Consumption
    if cn_consumption_kgpt is not None and \
       cn_consumption_kgpt > benchmark_config.cn_consumption_max_kgpt:
        weekly_flags.append({
            "rule_id": "WF-1",
            "rule_type": "WEEKLY_FLAG",
            "message": "Excessive cyanide consumption (kg/t) – economic risk.",
            "triggering_field": "cn_consumption_kgpt",
            "triggering_value": cn_consumption_kgpt,
            "benchmark_field": "cn_consumption_max_kgpt",
            "benchmark_value": benchmark_config.cn_consumption_max_kgpt,
        })
    
    # WF-2: Poor Cyanide Efficiency
    if cn_efficiency_gpkg is not None and \
       cn_efficiency_gpkg < benchmark_config.cn_efficiency_min_gpkg:
        weekly_flags.append({
            "rule_id": "WF-2",
            "rule_type": "WEEKLY_FLAG",
            "message": "Poor cyanide efficiency – approaching economic limit.",
            "triggering_field": "cn_efficiency_gpkg",
            "triggering_value": cn_efficiency_gpkg,
            "benchmark_field": "cn_efficiency_min_gpkg",
            "benchmark_value": benchmark_config.cn_efficiency_min_gpkg,
        })
    
    return weekly_flags


@router.post(
    "/weekly-control-summary",
    response_model=WeeklyControlSummaryWithAlertsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create weekly control summary",
    description="Creates a new weekly control summary with aggregated data from DailyControlLog. Requires Manager role or above.",
)
async def create_weekly_control_summary(
    summary_data: WeeklyControlSummaryCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_manager_or_above),
) -> WeeklyControlSummaryWithAlertsResponse:
    """
    Create a new weekly control summary with aggregated data.
    
    Requirements:
    - Requires Manager role or above
    - HeapConfig and BenchmarkConfig must exist
    - One summary per heap per week
    - Aggregates data from immutable DailyControlLog records
    
    Calculations:
    - weekly_solution_applied_m3: SUM of daily solution applied
    - weekly_pls_flow_m3: SUM of daily PLS flow
    - weekly_gold_in_pls_g: SUM of daily gold in PLS
    - cumulative_gold_in_pls_g: SUM of all weekly gold to date
    - contained_gold_g: heap_tonnage_t * head_grade_gpt
    - recovery_pct: (cumulative_gold_in_pls_g / contained_gold_g) * 100
    - cn_consumption_kgpt: cn_used_kg / heap_tonnage_t
    - cn_efficiency_gpkg: cumulative_gold_in_pls_g / cn_used_kg
    
    Weekly Flags (soft alerts):
    - WF-1: Excessive Cyanide Consumption
    - WF-2: Poor Cyanide Efficiency
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HeapConfig must exist before creating weekly summaries."
        )
    
    benchmark_config = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    if not benchmark_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BenchmarkConfig must exist before creating weekly summaries."
        )
    
    existing_summary = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config.id,
        WeeklyControlSummary.week_start_date == summary_data.week_start_date,
    ).first()
    if existing_summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A weekly summary already exists for week starting {summary_data.week_start_date}."
        )
    
    aggregation = aggregate_weekly_data(
        db, heap_config.id, summary_data.week_start_date, summary_data.week_end_date
    )
    
    previous_cumulative = calculate_cumulative_gold(
        db, heap_config.id, summary_data.week_start_date
    )
    cumulative_gold_in_pls_g = previous_cumulative + aggregation["weekly_gold_in_pls_g"]
    
    economic_metrics = calculate_economic_metrics(
        heap_config, cumulative_gold_in_pls_g, summary_data.cn_used_kg
    )
    
    db_summary = WeeklyControlSummary(
        heap_config_id=heap_config.id,
        week_start_date=summary_data.week_start_date,
        week_end_date=summary_data.week_end_date,
        cn_used_kg=summary_data.cn_used_kg,
        weekly_solution_applied_m3=aggregation["weekly_solution_applied_m3"],
        weekly_pls_flow_m3=aggregation["weekly_pls_flow_m3"],
        weekly_gold_in_pls_g=aggregation["weekly_gold_in_pls_g"],
        cumulative_gold_in_pls_g=round(cumulative_gold_in_pls_g, 6),
        contained_gold_g=economic_metrics["contained_gold_g"],
        recovery_pct=economic_metrics["recovery_pct"],
        cn_consumption_kgpt=economic_metrics["cn_consumption_kgpt"],
        cn_efficiency_gpkg=economic_metrics["cn_efficiency_gpkg"],
        created_by=current_user.id,
    )
    db.add(db_summary)
    db.flush()
    
    weekly_flags = evaluate_weekly_flags(
        economic_metrics["cn_consumption_kgpt"],
        economic_metrics["cn_efficiency_gpkg"],
        benchmark_config,
    )
    
    alert_logs = []
    for wf in weekly_flags:
        alert_log = ControlRuleLog(
            heap_config_id=heap_config.id,
            daily_control_log_id=None,
            rule_id=wf["rule_id"],
            rule_type=wf["rule_type"],
            rule_message=wf["message"],
            triggering_field=wf["triggering_field"],
            triggering_value=wf["triggering_value"],
            benchmark_field=wf["benchmark_field"],
            benchmark_value=wf["benchmark_value"],
            log_date=summary_data.week_end_date,
            created_by=current_user.id,
        )
        db.add(alert_log)
        alert_logs.append(alert_log)
    
    db.commit()
    db.refresh(db_summary)
    
    for alert_log in alert_logs:
        db.refresh(alert_log)
    
    aggregation_details = {
        "days_with_data": aggregation["days_with_data"],
        "aggregation_errors": aggregation["errors"],
        "economic_calculation_errors": economic_metrics["errors"],
    }
    
    return WeeklyControlSummaryWithAlertsResponse(
        weekly_summary=WeeklyControlSummaryResponse.model_validate(db_summary),
        alerts=[ControlRuleLogResponse.model_validate(log) for log in alert_logs],
        aggregation_details=aggregation_details,
    )


@router.get(
    "/weekly-control-summary",
    response_model=List[WeeklyControlSummaryResponse],
    summary="List weekly control summaries",
    description="Returns all weekly control summaries for the heap. All authenticated users can read summaries.",
)
async def list_weekly_control_summaries(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
    limit: int = Query(default=52, ge=1, le=520, description="Maximum number of summaries to return"),
    offset: int = Query(default=0, ge=0, description="Number of summaries to skip"),
) -> List[WeeklyControlSummaryResponse]:
    """
    List weekly control summaries with pagination.
    
    All authenticated users can read weekly summaries.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. No summaries available."
        )
    
    summaries = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config.id
    ).order_by(WeeklyControlSummary.week_start_date.desc()).offset(offset).limit(limit).all()
    
    return [WeeklyControlSummaryResponse.model_validate(s) for s in summaries]


@router.get(
    "/weekly-control-summary/{week_start_date}",
    response_model=WeeklyControlSummaryResponse,
    summary="Get weekly control summary by week start date",
    description="Returns the weekly control summary for a specific week. All authenticated users can read summaries.",
)
async def get_weekly_control_summary(
    week_start_date: date,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
) -> WeeklyControlSummaryResponse:
    """
    Get the weekly control summary for a specific week.
    
    All authenticated users can read weekly summaries.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found."
        )
    
    summary = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config.id,
        WeeklyControlSummary.week_start_date == week_start_date,
    ).first()
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No weekly summary found for week starting {week_start_date}."
        )
    
    return WeeklyControlSummaryResponse.model_validate(summary)


def evaluate_stop_leach_decision(
    weekly_summary: WeeklyControlSummary,
    benchmark_config: BenchmarkConfig,
) -> Dict[str, Any]:
    """
    Evaluate whether to recommend stopping leaching based on weekly metrics.
    
    Decision Logic:
    - stop_recommendation = TRUE if any economic threshold is breached
    - Thresholds: cn_efficiency below minimum, cn_consumption above maximum
    
    Returns:
    - stop_recommendation: 0 (continue) or 1 (stop)
    - decision_reasons: List of reasons for the recommendation
    - metrics: Snapshot of metrics used for decision
    """
    decision_reasons = []
    stop_recommendation = 0
    
    if weekly_summary.cn_efficiency_gpkg is not None and \
       weekly_summary.cn_efficiency_gpkg < benchmark_config.cn_efficiency_min_gpkg:
        decision_reasons.append(
            f"Cyanide efficiency ({weekly_summary.cn_efficiency_gpkg:.4f} g/kg) below minimum ({benchmark_config.cn_efficiency_min_gpkg} g/kg)"
        )
        stop_recommendation = 1
    
    if weekly_summary.cn_consumption_kgpt is not None and \
       weekly_summary.cn_consumption_kgpt > benchmark_config.cn_consumption_max_kgpt:
        decision_reasons.append(
            f"Cyanide consumption ({weekly_summary.cn_consumption_kgpt:.4f} kg/t) above maximum ({benchmark_config.cn_consumption_max_kgpt} kg/t)"
        )
        stop_recommendation = 1
    
    if weekly_summary.recovery_pct is not None and weekly_summary.recovery_pct < 10.0:
        decision_reasons.append(
            f"Recovery percentage ({weekly_summary.recovery_pct:.2f}%) critically low"
        )
        stop_recommendation = 1
    
    if not decision_reasons:
        decision_reasons.append("All metrics within acceptable ranges - continue leaching")
    
    return {
        "stop_recommendation": stop_recommendation,
        "decision_reasons": decision_reasons,
        "metrics": {
            "recovery_pct": weekly_summary.recovery_pct,
            "cn_efficiency_gpkg": weekly_summary.cn_efficiency_gpkg,
            "cn_consumption_kgpt": weekly_summary.cn_consumption_kgpt,
            "cumulative_gold_in_pls_g": weekly_summary.cumulative_gold_in_pls_g,
        },
    }


@router.post(
    "/stop-leach-decision/{weekly_summary_id}",
    response_model=StopLeachDecisionWithOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate stop-leach decision",
    description="Generates a stop-leach decision based on weekly metrics. Requires Manager role or above.",
)
async def create_stop_leach_decision(
    weekly_summary_id: str,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_manager_or_above),
) -> StopLeachDecisionWithOverrideResponse:
    """
    Generate a stop-leach decision for a weekly summary.
    
    Requirements:
    - Requires Manager role or above
    - WeeklyControlSummary must exist
    - One decision per weekly summary
    
    Decision Logic:
    - Evaluates economic metrics against benchmarks
    - stop_recommendation = 1 if thresholds breached
    - Decision is IMMUTABLE after creation
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HeapConfig must exist."
        )
    
    benchmark_config = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    if not benchmark_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BenchmarkConfig must exist."
        )
    
    weekly_summary = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.id == weekly_summary_id,
        WeeklyControlSummary.heap_config_id == heap_config.id,
    ).first()
    if not weekly_summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WeeklyControlSummary with ID {weekly_summary_id} not found."
        )
    
    existing_decision = db.query(StopLeachDecision).filter(
        StopLeachDecision.weekly_summary_id == weekly_summary_id,
    ).first()
    if existing_decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A stop-leach decision already exists for this weekly summary."
        )
    
    evaluation = evaluate_stop_leach_decision(weekly_summary, benchmark_config)
    
    system_status = "STOP" if evaluation["stop_recommendation"] == 1 else "CONTINUE"
    
    db_decision = StopLeachDecision(
        heap_config_id=heap_config.id,
        weekly_summary_id=weekly_summary_id,
        decision_date=weekly_summary.week_end_date,
        stop_recommendation=evaluation["stop_recommendation"],
        recovery_pct=evaluation["metrics"]["recovery_pct"],
        cn_efficiency_gpkg=evaluation["metrics"]["cn_efficiency_gpkg"],
        cn_consumption_kgpt=evaluation["metrics"]["cn_consumption_kgpt"],
        cumulative_gold_in_pls_g=evaluation["metrics"]["cumulative_gold_in_pls_g"],
        decision_reasons=evaluation["decision_reasons"],
        system_status=system_status,
        created_by=current_user.id,
    )
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)
    
    return StopLeachDecisionWithOverrideResponse(
        decision=StopLeachDecisionResponse.model_validate(db_decision),
        override=None,
        effective_status=system_status,
    )


@router.get(
    "/stop-leach-decision",
    response_model=List[StopLeachDecisionWithOverrideResponse],
    summary="List stop-leach decisions",
    description="Returns all stop-leach decisions with any overrides. All authenticated users can read decisions.",
)
async def list_stop_leach_decisions(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
    limit: int = Query(default=52, ge=1, le=520, description="Maximum number of decisions to return"),
    offset: int = Query(default=0, ge=0, description="Number of decisions to skip"),
) -> List[StopLeachDecisionWithOverrideResponse]:
    """
    List stop-leach decisions with any overrides.
    
    All authenticated users can read decisions.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. No decisions available."
        )
    
    decisions = db.query(StopLeachDecision).filter(
        StopLeachDecision.heap_config_id == heap_config.id
    ).order_by(StopLeachDecision.decision_date.desc()).offset(offset).limit(limit).all()
    
    results = []
    for decision in decisions:
        override = db.query(StopLeachOverride).filter(
            StopLeachOverride.decision_id == decision.id
        ).first()
        
        effective_status = decision.system_status
        if override:
            if override.override_action == "CONTINUE":
                effective_status = "CONTINUE_UNDER_OVERRIDE"
            else:
                effective_status = "STOP_CONFIRMED_BY_MANAGEMENT"
        
        results.append(StopLeachDecisionWithOverrideResponse(
            decision=StopLeachDecisionResponse.model_validate(decision),
            override=StopLeachOverrideResponse.model_validate(override) if override else None,
            effective_status=effective_status,
        ))
    
    return results


@router.get(
    "/stop-leach-decision/{decision_id}",
    response_model=StopLeachDecisionWithOverrideResponse,
    summary="Get stop-leach decision by ID",
    description="Returns a specific stop-leach decision with any override. All authenticated users can read decisions.",
)
async def get_stop_leach_decision(
    decision_id: str,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
) -> StopLeachDecisionWithOverrideResponse:
    """
    Get a specific stop-leach decision with any override.
    
    All authenticated users can read decisions.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found."
        )
    
    decision = db.query(StopLeachDecision).filter(
        StopLeachDecision.id == decision_id,
        StopLeachDecision.heap_config_id == heap_config.id,
    ).first()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StopLeachDecision with ID {decision_id} not found."
        )
    
    override = db.query(StopLeachOverride).filter(
        StopLeachOverride.decision_id == decision.id
    ).first()
    
    effective_status = decision.system_status
    if override:
        if override.override_action == "CONTINUE":
            effective_status = "CONTINUE_UNDER_OVERRIDE"
        else:
            effective_status = "STOP_CONFIRMED_BY_MANAGEMENT"
    
    return StopLeachDecisionWithOverrideResponse(
        decision=StopLeachDecisionResponse.model_validate(decision),
        override=StopLeachOverrideResponse.model_validate(override) if override else None,
        effective_status=effective_status,
    )


@router.post(
    "/stop-leach-override",
    response_model=StopLeachDecisionWithOverrideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create management override",
    description="Creates a management override for a stop-leach decision. Requires Manager role. Only allowed for decisions with stop_recommendation == TRUE.",
)
async def create_stop_leach_override(
    override_data: StopLeachOverrideCreate,
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_manager_or_above),
) -> StopLeachDecisionWithOverrideResponse:
    """
    Create a management override for a stop-leach decision.
    
    Requirements:
    - Requires Manager role
    - StopLeachDecision must exist with stop_recommendation == TRUE
    - One override per decision
    - Override cannot be edited or deleted once submitted
    
    Override Actions:
    - CONTINUE: System status becomes "CONTINUE_UNDER_OVERRIDE"
    - STOP: System status becomes "STOP_CONFIRMED_BY_MANAGEMENT"
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HeapConfig must exist."
        )
    
    decision = db.query(StopLeachDecision).filter(
        StopLeachDecision.id == override_data.decision_id,
        StopLeachDecision.heap_config_id == heap_config.id,
    ).first()
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"StopLeachDecision with ID {override_data.decision_id} not found."
        )
    
    if decision.stop_recommendation != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Override can only be created for decisions with stop_recommendation == TRUE (1)."
        )
    
    existing_override = db.query(StopLeachOverride).filter(
        StopLeachOverride.decision_id == override_data.decision_id,
    ).first()
    if existing_override:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An override already exists for this decision. Overrides cannot be edited or deleted."
        )
    
    decision_snapshot = {
        "id": decision.id,
        "decision_date": str(decision.decision_date),
        "stop_recommendation": decision.stop_recommendation,
        "recovery_pct": decision.recovery_pct,
        "cn_efficiency_gpkg": decision.cn_efficiency_gpkg,
        "cn_consumption_kgpt": decision.cn_consumption_kgpt,
        "cumulative_gold_in_pls_g": decision.cumulative_gold_in_pls_g,
        "decision_reasons": decision.decision_reasons,
        "original_system_status": decision.system_status,
    }
    
    db_override = StopLeachOverride(
        heap_config_id=heap_config.id,
        decision_id=override_data.decision_id,
        override_action=override_data.override_action.value,
        override_reason=override_data.override_reason.value,
        override_justification_text=override_data.override_justification_text,
        decision_snapshot=decision_snapshot,
        override_by=current_user.id,
    )
    db.add(db_override)
    
    if override_data.override_action.value == "CONTINUE":
        decision.system_status = "CONTINUE_UNDER_OVERRIDE"
    else:
        decision.system_status = "STOP_CONFIRMED_BY_MANAGEMENT"
    
    db.commit()
    db.refresh(db_override)
    db.refresh(decision)
    
    return StopLeachDecisionWithOverrideResponse(
        decision=StopLeachDecisionResponse.model_validate(decision),
        override=StopLeachOverrideResponse.model_validate(db_override),
        effective_status=decision.system_status,
    )


@router.get(
    "/stop-leach-override",
    response_model=List[StopLeachOverrideResponse],
    summary="List all overrides",
    description="Returns all stop-leach overrides for audit purposes. All authenticated users can read overrides.",
)
async def list_stop_leach_overrides(
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of overrides to return"),
    offset: int = Query(default=0, ge=0, description="Number of overrides to skip"),
) -> List[StopLeachOverrideResponse]:
    """
    List all stop-leach overrides for audit purposes.
    
    All authenticated users can read overrides.
    Overrides are immutable - no update or delete operations available.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HeapConfig not found. No overrides available."
        )
    
    overrides = db.query(StopLeachOverride).filter(
        StopLeachOverride.heap_config_id == heap_config.id
    ).order_by(StopLeachOverride.override_timestamp.desc()).offset(offset).limit(limit).all()
    
    return [StopLeachOverrideResponse.model_validate(o) for o in overrides]


@router.get(
    "/export/daily-logs",
    summary="Export daily control logs",
    description="Export daily control logs in JSON or CSV format. All authenticated users can export.",
)
async def export_daily_logs(
    format: str = Query(default="json", description="Export format: json or csv"),
    start_date: Optional[date] = Query(default=None, description="Start date filter"),
    end_date: Optional[date] = Query(default=None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
):
    """Export daily control logs with derived fields and alerts."""
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(status_code=404, detail="HeapConfig not found.")
    
    query = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config.id
    )
    
    if start_date:
        query = query.filter(DailyControlLog.log_date >= start_date)
    if end_date:
        query = query.filter(DailyControlLog.log_date <= end_date)
    
    logs = query.order_by(DailyControlLog.log_date).all()
    
    export_data = []
    for log in logs:
        solution_applied_m3 = log.flow_m3_per_hr * log.irrigation_hours
        application_rate = (log.flow_m3_per_hr * 1000) / log.area_irrigated_m2 if log.area_irrigated_m2 > 0 else None
        pls_return_pct = (log.pls_flow_m3 / solution_applied_m3) * 100 if solution_applied_m3 > 0 else None
        gold_in_pls_g = log.pls_au_mgL * log.pls_flow_m3
        leach_day = (log.log_date - heap_config.leach_start_date).days + 1
        
        alerts = db.query(ControlRuleLog).filter(
            ControlRuleLog.daily_control_log_id == log.id
        ).all()
        
        record = {
            "log_date": str(log.log_date),
            "leach_day": leach_day,
            "area_irrigated_m2": log.area_irrigated_m2,
            "flow_m3_per_hr": log.flow_m3_per_hr,
            "irrigation_hours": log.irrigation_hours,
            "applied_cn_ppm": log.applied_cn_ppm,
            "applied_ph": log.applied_ph,
            "pls_flow_m3": log.pls_flow_m3,
            "pls_au_mgL": log.pls_au_mgL,
            "pond_freeboard_m": log.pond_freeboard_m,
            "solution_applied_m3": solution_applied_m3,
            "application_rate_L_m2_hr": application_rate,
            "pls_return_pct": pls_return_pct,
            "gold_in_pls_g": gold_in_pls_g,
            "alerts": [{"rule_id": a.rule_id, "message": a.rule_message} for a in alerts],
            "created_at": str(log.created_at),
            "created_by": log.created_by,
        }
        export_data.append(record)
    
    if format.lower() == "csv":
        output = io.StringIO()
        if export_data:
            fieldnames = [k for k in export_data[0].keys() if k != "alerts"]
            fieldnames.append("alert_count")
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for record in export_data:
                row = {k: v for k, v in record.items() if k != "alerts"}
                row["alert_count"] = len(record["alerts"])
                writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=daily_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    
    return JSONResponse(content={
        "module_id": "heap_leaching_key_controls",
        "module_version": "1.0.0",
        "heap_id": heap_config.heap_id,
        "export_timestamp": datetime.utcnow().isoformat(),
        "exported_by": current_user.id,
        "record_count": len(export_data),
        "data": export_data,
    })


@router.get(
    "/export/weekly-summaries",
    summary="Export weekly control summaries",
    description="Export weekly control summaries in JSON or CSV format. All authenticated users can export.",
)
async def export_weekly_summaries(
    format: str = Query(default="json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
):
    """Export weekly control summaries with economic metrics."""
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(status_code=404, detail="HeapConfig not found.")
    
    summaries = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config.id
    ).order_by(WeeklyControlSummary.week_start_date).all()
    
    alerts = db.query(ControlRuleLog).filter(
        ControlRuleLog.heap_config_id == heap_config.id,
        ControlRuleLog.rule_type == "WEEKLY_FLAG"
    ).all()
    alerts_by_date = {}
    for alert in alerts:
        key = str(alert.log_date)
        if key not in alerts_by_date:
            alerts_by_date[key] = []
        alerts_by_date[key].append(alert)
    
    export_data = []
    for summary in summaries:
        week_alerts = alerts_by_date.get(str(summary.week_end_date), [])
        record = {
            "week_start_date": str(summary.week_start_date),
            "week_end_date": str(summary.week_end_date),
            "cn_used_kg": summary.cn_used_kg,
            "weekly_solution_applied_m3": summary.weekly_solution_applied_m3,
            "weekly_pls_flow_m3": summary.weekly_pls_flow_m3,
            "weekly_gold_in_pls_g": summary.weekly_gold_in_pls_g,
            "cumulative_gold_in_pls_g": summary.cumulative_gold_in_pls_g,
            "contained_gold_g": summary.contained_gold_g,
            "recovery_pct": summary.recovery_pct,
            "cn_consumption_kgpt": summary.cn_consumption_kgpt,
            "cn_efficiency_gpkg": summary.cn_efficiency_gpkg,
            "is_approved": summary.is_approved,
            "flags": [{"rule_id": a.rule_id, "message": a.rule_message} for a in week_alerts],
            "created_at": str(summary.created_at),
        }
        export_data.append(record)
    
    if format.lower() == "csv":
        output = io.StringIO()
        if export_data:
            fieldnames = [k for k in export_data[0].keys() if k != "flags"]
            fieldnames.append("flag_count")
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for record in export_data:
                row = {k: v for k, v in record.items() if k != "flags"}
                row["flag_count"] = len(record["flags"])
                writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=weekly_summaries_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    
    return JSONResponse(content={
        "module_id": "heap_leaching_key_controls",
        "module_version": "1.0.0",
        "heap_id": heap_config.heap_id,
        "export_timestamp": datetime.utcnow().isoformat(),
        "exported_by": current_user.id,
        "record_count": len(export_data),
        "data": export_data,
    })


@router.get(
    "/export/decisions",
    summary="Export stop-leach decisions",
    description="Export stop-leach decisions with overrides in JSON or CSV format. All authenticated users can export.",
)
async def export_decisions(
    format: str = Query(default="json", description="Export format: json or csv"),
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
):
    """Export stop-leach decisions with triggered rules and overrides."""
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(status_code=404, detail="HeapConfig not found.")
    
    decisions = db.query(StopLeachDecision).filter(
        StopLeachDecision.heap_config_id == heap_config.id
    ).order_by(StopLeachDecision.decision_date).all()
    
    export_data = []
    for decision in decisions:
        override = db.query(StopLeachOverride).filter(
            StopLeachOverride.decision_id == decision.id
        ).first()
        
        effective_status = decision.system_status
        if override:
            if override.override_action == "CONTINUE":
                effective_status = "CONTINUE_UNDER_OVERRIDE"
            else:
                effective_status = "STOP_CONFIRMED_BY_MANAGEMENT"
        
        record = {
            "decision_id": decision.id,
            "decision_date": str(decision.decision_date),
            "stop_recommendation": decision.stop_recommendation,
            "system_status": decision.system_status,
            "effective_status": effective_status,
            "recovery_pct": decision.recovery_pct,
            "cn_efficiency_gpkg": decision.cn_efficiency_gpkg,
            "cn_consumption_kgpt": decision.cn_consumption_kgpt,
            "cumulative_gold_in_pls_g": decision.cumulative_gold_in_pls_g,
            "decision_reasons": decision.decision_reasons,
            "has_override": override is not None,
            "override_action": override.override_action if override else None,
            "override_reason": override.override_reason if override else None,
            "override_justification": override.override_justification_text if override else None,
            "override_by": override.override_by if override else None,
            "override_timestamp": str(override.override_timestamp) if override else None,
            "created_at": str(decision.created_at),
        }
        export_data.append(record)
    
    if format.lower() == "csv":
        output = io.StringIO()
        if export_data:
            fieldnames = [k for k in export_data[0].keys() if k != "decision_reasons"]
            fieldnames.append("reason_count")
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for record in export_data:
                row = {k: v for k, v in record.items() if k != "decision_reasons"}
                row["reason_count"] = len(record["decision_reasons"]) if record["decision_reasons"] else 0
                writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=decisions_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    
    return JSONResponse(content={
        "module_id": "heap_leaching_key_controls",
        "module_version": "1.0.0",
        "heap_id": heap_config.heap_id,
        "export_timestamp": datetime.utcnow().isoformat(),
        "exported_by": current_user.id,
        "record_count": len(export_data),
        "data": export_data,
    })


@router.get(
    "/dashboard/daily",
    summary="Daily operations dashboard",
    description="Read-only dashboard showing daily control logs with status indicators. Access based on role.",
)
async def dashboard_daily(
    start_date: Optional[date] = Query(default=None, description="Start date filter"),
    end_date: Optional[date] = Query(default=None, description="End date filter"),
    limit: int = Query(default=30, ge=1, le=365, description="Maximum records to return"),
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(get_current_active_user),
):
    """
    Daily operations dashboard (read-only).
    
    Shows daily control logs with:
    - Input values and derived calculations
    - Status indicators (green/amber/red)
    - Alerts and hard stops
    
    Access:
    - Contractor: can view own submissions only
    - Engineer/Manager/Admin: can view all
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(status_code=404, detail="HeapConfig not found.")
    
    benchmark = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    
    query = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config.id
    )
    
    if current_user.role == "operator":
        query = query.filter(DailyControlLog.created_by == current_user.id)
    
    if start_date:
        query = query.filter(DailyControlLog.log_date >= start_date)
    if end_date:
        query = query.filter(DailyControlLog.log_date <= end_date)
    
    logs = query.order_by(DailyControlLog.log_date.desc()).limit(limit).all()
    
    dashboard_data = []
    for log in logs:
        solution_applied_m3 = log.flow_m3_per_hr * log.irrigation_hours
        application_rate = (log.flow_m3_per_hr * 1000) / log.area_irrigated_m2 if log.area_irrigated_m2 > 0 else None
        pls_return_pct = (log.pls_flow_m3 / solution_applied_m3) * 100 if solution_applied_m3 > 0 else None
        gold_in_pls_g = log.pls_au_mgL * log.pls_flow_m3
        leach_day = (log.log_date - heap_config.leach_start_date).days + 1
        
        alerts = db.query(ControlRuleLog).filter(
            ControlRuleLog.daily_control_log_id == log.id
        ).all()
        
        hard_stops = [a for a in alerts if a.rule_type == "HARD_STOP"]
        soft_alerts = [a for a in alerts if a.rule_type == "SOFT_ALERT"]
        
        if hard_stops:
            overall_status = "red"
        elif soft_alerts:
            overall_status = "amber"
        else:
            overall_status = "green"
        
        ph_status = "green"
        if benchmark and log.applied_ph < benchmark.ph_min:
            ph_status = "red"
        elif benchmark and log.applied_ph > benchmark.ph_max:
            ph_status = "amber"
        
        freeboard_status = "green"
        if benchmark and log.pond_freeboard_m < benchmark.pond_freeboard_min_m:
            freeboard_status = "red"
        
        app_rate_status = "green"
        if benchmark and application_rate:
            if application_rate < benchmark.application_rate_min_L_m2_hr or application_rate > benchmark.application_rate_max_L_m2_hr:
                app_rate_status = "amber"
        
        cn_status = "green"
        if benchmark:
            if log.applied_cn_ppm < benchmark.cn_min_ppm or log.applied_cn_ppm > benchmark.cn_max_ppm:
                cn_status = "amber"
        
        pls_return_status = "green"
        if benchmark and pls_return_pct and pls_return_pct < benchmark.pls_return_min_pct:
            pls_return_status = "amber"
        
        gold_status = "green"
        if log.pls_au_mgL == 0:
            gold_status = "amber"
        elif benchmark and log.pls_au_mgL < benchmark.pls_low_au_mgL:
            gold_status = "amber"
        
        record = {
            "log_date": str(log.log_date),
            "leach_day": leach_day,
            "overall_status": overall_status,
            "inputs": {
                "area_irrigated_m2": log.area_irrigated_m2,
                "flow_m3_per_hr": log.flow_m3_per_hr,
                "irrigation_hours": log.irrigation_hours,
                "applied_cn_ppm": {"value": log.applied_cn_ppm, "status": cn_status},
                "applied_ph": {"value": log.applied_ph, "status": ph_status},
                "pls_flow_m3": log.pls_flow_m3,
                "pls_au_mgL": {"value": log.pls_au_mgL, "status": gold_status},
                "pond_freeboard_m": {"value": log.pond_freeboard_m, "status": freeboard_status},
            },
            "derived": {
                "solution_applied_m3": solution_applied_m3,
                "application_rate_L_m2_hr": {"value": application_rate, "status": app_rate_status},
                "pls_return_pct": {"value": pls_return_pct, "status": pls_return_status},
                "gold_in_pls_g": gold_in_pls_g,
            },
            "alerts": {
                "hard_stops": [{"rule_id": a.rule_id, "message": a.rule_message} for a in hard_stops],
                "soft_alerts": [{"rule_id": a.rule_id, "message": a.rule_message} for a in soft_alerts],
            },
        }
        dashboard_data.append(record)
    
    return {
        "dashboard": "daily_operations",
        "heap_id": heap_config.heap_id,
        "heap_tonnage_t": heap_config.heap_tonnage_t,
        "leach_start_date": str(heap_config.leach_start_date),
        "record_count": len(dashboard_data),
        "data": dashboard_data,
    }


@router.get(
    "/dashboard/weekly",
    summary="Weekly summary dashboard",
    description="Read-only dashboard showing weekly summaries with economic metrics. Engineer+ access.",
)
async def dashboard_weekly(
    limit: int = Query(default=12, ge=1, le=52, description="Maximum weeks to return"),
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_engineer_or_above),
):
    """
    Weekly summary dashboard (read-only).
    
    Shows weekly control summaries with:
    - Aggregated metrics
    - Economic indicators
    - Status indicators (green/amber/red)
    - Weekly flags
    
    Access: Engineer, Manager, Admin only
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(status_code=404, detail="HeapConfig not found.")
    
    benchmark = db.query(BenchmarkConfig).filter(
        BenchmarkConfig.heap_config_id == heap_config.id
    ).first()
    
    summaries = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config.id
    ).order_by(WeeklyControlSummary.week_start_date.desc()).limit(limit).all()
    
    dashboard_data = []
    for summary in summaries:
        flags = db.query(ControlRuleLog).filter(
            ControlRuleLog.heap_config_id == heap_config.id,
            ControlRuleLog.rule_type == "WEEKLY_FLAG",
            ControlRuleLog.log_date == summary.week_end_date,
        ).all()
        
        cn_consumption_status = "green"
        if benchmark and summary.cn_consumption_kgpt:
            if summary.cn_consumption_kgpt > benchmark.cn_consumption_max_kgpt:
                cn_consumption_status = "red"
            elif summary.cn_consumption_kgpt > benchmark.cn_consumption_max_kgpt * 0.8:
                cn_consumption_status = "amber"
        
        cn_efficiency_status = "green"
        if benchmark and summary.cn_efficiency_gpkg:
            if summary.cn_efficiency_gpkg < benchmark.cn_efficiency_min_gpkg:
                cn_efficiency_status = "red"
            elif summary.cn_efficiency_gpkg < benchmark.cn_efficiency_min_gpkg * 1.2:
                cn_efficiency_status = "amber"
        
        recovery_status = "green"
        if summary.recovery_pct:
            if summary.recovery_pct < 10:
                recovery_status = "red"
            elif summary.recovery_pct < 30:
                recovery_status = "amber"
        
        if flags:
            overall_status = "amber"
        else:
            overall_status = "green"
        
        if cn_consumption_status == "red" or cn_efficiency_status == "red" or recovery_status == "red":
            overall_status = "red"
        
        record = {
            "week_start_date": str(summary.week_start_date),
            "week_end_date": str(summary.week_end_date),
            "overall_status": overall_status,
            "aggregated": {
                "cn_used_kg": summary.cn_used_kg,
                "weekly_solution_applied_m3": summary.weekly_solution_applied_m3,
                "weekly_pls_flow_m3": summary.weekly_pls_flow_m3,
                "weekly_gold_in_pls_g": summary.weekly_gold_in_pls_g,
            },
            "cumulative": {
                "cumulative_gold_in_pls_g": summary.cumulative_gold_in_pls_g,
                "contained_gold_g": summary.contained_gold_g,
            },
            "economic": {
                "recovery_pct": {"value": summary.recovery_pct, "status": recovery_status},
                "cn_consumption_kgpt": {"value": summary.cn_consumption_kgpt, "status": cn_consumption_status},
                "cn_efficiency_gpkg": {"value": summary.cn_efficiency_gpkg, "status": cn_efficiency_status},
            },
            "flags": [{"rule_id": f.rule_id, "message": f.rule_message} for f in flags],
            "is_approved": summary.is_approved,
        }
        dashboard_data.append(record)
    
    return {
        "dashboard": "weekly_summary",
        "heap_id": heap_config.heap_id,
        "heap_tonnage_t": heap_config.heap_tonnage_t,
        "head_grade_gpt": heap_config.head_grade_gpt,
        "record_count": len(dashboard_data),
        "data": dashboard_data,
    }


@router.get(
    "/dashboard/decisions",
    summary="Stop-leach decisions dashboard",
    description="Read-only dashboard showing stop-leach decisions and overrides. Engineer+ access.",
)
async def dashboard_decisions(
    limit: int = Query(default=12, ge=1, le=52, description="Maximum decisions to return"),
    db: Session = Depends(get_db),
    current_user: user_models.User = Depends(require_engineer_or_above),
):
    """
    Stop-leach decisions dashboard (read-only).
    
    Shows stop-leach decisions with:
    - System recommendation (STOP/CONTINUE)
    - Triggered rules
    - Management overrides (if any)
    - Effective status
    
    Access: Engineer, Manager, Admin only
    Contractor cannot view this dashboard.
    """
    heap_config = db.query(HeapConfig).first()
    if not heap_config:
        raise HTTPException(status_code=404, detail="HeapConfig not found.")
    
    decisions = db.query(StopLeachDecision).filter(
        StopLeachDecision.heap_config_id == heap_config.id
    ).order_by(StopLeachDecision.decision_date.desc()).limit(limit).all()
    
    dashboard_data = []
    for decision in decisions:
        override = db.query(StopLeachOverride).filter(
            StopLeachOverride.decision_id == decision.id
        ).first()
        
        effective_status = decision.system_status
        if override:
            if override.override_action == "CONTINUE":
                effective_status = "CONTINUE_UNDER_OVERRIDE"
            else:
                effective_status = "STOP_CONFIRMED_BY_MANAGEMENT"
        
        if decision.stop_recommendation == 1:
            recommendation_status = "red"
        else:
            recommendation_status = "green"
        
        if effective_status in ["CONTINUE", "CONTINUE_UNDER_OVERRIDE"]:
            effective_status_color = "green" if effective_status == "CONTINUE" else "amber"
        else:
            effective_status_color = "red"
        
        record = {
            "decision_id": decision.id,
            "decision_date": str(decision.decision_date),
            "recommendation": {
                "stop_recommendation": decision.stop_recommendation,
                "status": recommendation_status,
                "reasons": decision.decision_reasons,
            },
            "metrics": {
                "recovery_pct": decision.recovery_pct,
                "cn_efficiency_gpkg": decision.cn_efficiency_gpkg,
                "cn_consumption_kgpt": decision.cn_consumption_kgpt,
                "cumulative_gold_in_pls_g": decision.cumulative_gold_in_pls_g,
            },
            "system_status": decision.system_status,
            "effective_status": {
                "value": effective_status,
                "color": effective_status_color,
            },
            "override": {
                "has_override": override is not None,
                "action": override.override_action if override else None,
                "reason": override.override_reason if override else None,
                "justification": override.override_justification_text if override else None,
                "override_by": override.override_by if override else None,
                "override_timestamp": str(override.override_timestamp) if override else None,
            } if override else None,
        }
        dashboard_data.append(record)
    
    return {
        "dashboard": "stop_leach_decisions",
        "heap_id": heap_config.heap_id,
        "record_count": len(dashboard_data),
        "data": dashboard_data,
    }
