"""
Seed demo data for Heap Leaching module staging environment.

Creates:
- Demo users (contractor, engineer, manager)
- HeapConfig (HEAP-001)
- BenchmarkConfig (oxide defaults)
- Sample DailyControlLog entries
- Sample WeeklyControlSummary
- Sample StopLeachDecision with override
"""

import os
import sys
from datetime import date, datetime, timedelta
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import get_password_hash
from modules.heap_leaching.models import (
    HeapConfig, BenchmarkConfig, DailyControlLog, ControlRuleLog,
    WeeklyControlSummary, StopLeachDecision, StopLeachOverride
)


def create_demo_users(db: Session):
    """Create demo users for staging."""
    users = []
    
    contractor = models.User(
        id=str(uuid4()),
        name="Demo Contractor",
        email="contractor_demo@klusetic.com",
        hashed_password=get_password_hash("demo123"),
        role="operator",
        is_active=True,
    )
    users.append(contractor)
    
    engineer = models.User(
        id=str(uuid4()),
        name="Demo Engineer",
        email="engineer_demo@klusetic.com",
        hashed_password=get_password_hash("demo123"),
        role="supervisor",
        is_active=True,
    )
    users.append(engineer)
    
    manager = models.User(
        id=str(uuid4()),
        name="Demo Manager",
        email="manager_demo@klusetic.com",
        hashed_password=get_password_hash("demo123"),
        role="manager",
        is_active=True,
    )
    users.append(manager)
    
    admin = models.User(
        id=str(uuid4()),
        name="Demo Admin",
        email="admin_demo@klusetic.com",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    users.append(admin)
    
    for user in users:
        existing = db.query(models.User).filter(models.User.email == user.email).first()
        if not existing:
            db.add(user)
            print(f"Created user: {user.email}")
        else:
            print(f"User already exists: {user.email}")
    
    db.commit()
    return {
        "contractor": contractor if not db.query(models.User).filter(models.User.email == "contractor_demo@klusetic.com").first() else db.query(models.User).filter(models.User.email == "contractor_demo@klusetic.com").first(),
        "engineer": engineer if not db.query(models.User).filter(models.User.email == "engineer_demo@klusetic.com").first() else db.query(models.User).filter(models.User.email == "engineer_demo@klusetic.com").first(),
        "manager": manager if not db.query(models.User).filter(models.User.email == "manager_demo@klusetic.com").first() else db.query(models.User).filter(models.User.email == "manager_demo@klusetic.com").first(),
        "admin": admin if not db.query(models.User).filter(models.User.email == "admin_demo@klusetic.com").first() else db.query(models.User).filter(models.User.email == "admin_demo@klusetic.com").first(),
    }


def create_heap_config(db: Session, manager_id: str):
    """Create HeapConfig for HEAP-001."""
    existing = db.query(HeapConfig).filter(HeapConfig.heap_id == "HEAP-001").first()
    if existing:
        print("HeapConfig HEAP-001 already exists")
        return existing
    
    heap_config = HeapConfig(
        id=str(uuid4()),
        heap_id="HEAP-001",
        heap_tonnage_t=1000.0,
        head_grade_gpt=2.0,
        leach_start_date=date(2025, 1, 1),
        version=1,
        created_by=manager_id,
        updated_by=manager_id,
    )
    db.add(heap_config)
    db.commit()
    db.refresh(heap_config)
    print(f"Created HeapConfig: {heap_config.heap_id}")
    return heap_config


def create_benchmark_config(db: Session, heap_config_id: str, admin_id: str):
    """Create BenchmarkConfig with oxide defaults."""
    existing = db.query(BenchmarkConfig).filter(BenchmarkConfig.heap_config_id == heap_config_id).first()
    if existing:
        print("BenchmarkConfig already exists")
        return existing
    
    benchmark = BenchmarkConfig(
        id=str(uuid4()),
        heap_config_id=heap_config_id,
        application_rate_min_L_m2_hr=8.0,
        application_rate_max_L_m2_hr=12.0,
        cn_min_ppm=200.0,
        cn_max_ppm=500.0,
        ph_min=10.5,
        ph_max=11.0,
        pls_return_min_pct=80.0,
        pond_freeboard_min_m=0.5,
        cn_consumption_max_kgpt=2.0,
        cn_efficiency_min_gpkg=0.5,
        pls_low_au_mgL=0.2,
        version=1,
        created_by=admin_id,
        updated_by=admin_id,
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    print("Created BenchmarkConfig")
    return benchmark


def create_daily_logs(db: Session, heap_config_id: str, contractor_id: str, start_date: date, days: int, scenario: str = "normal"):
    """Create DailyControlLog entries."""
    logs = []
    
    for day in range(days):
        log_date = start_date + timedelta(days=day)
        
        existing = db.query(DailyControlLog).filter(
            DailyControlLog.heap_config_id == heap_config_id,
            DailyControlLog.log_date == log_date
        ).first()
        if existing:
            logs.append(existing)
            continue
        
        if scenario == "normal":
            pls_au_mgL = 0.5
            applied_cn_ppm = 300.0
        elif scenario == "low_gold":
            pls_au_mgL = 0.1
            applied_cn_ppm = 300.0
        else:
            pls_au_mgL = 0.5
            applied_cn_ppm = 300.0
        
        log = DailyControlLog(
            id=str(uuid4()),
            heap_config_id=heap_config_id,
            log_date=log_date,
            area_irrigated_m2=1000.0,
            flow_m3_per_hr=10.0,
            irrigation_hours=20.0,
            applied_cn_ppm=applied_cn_ppm,
            applied_ph=10.8,
            pls_flow_m3=180.0,
            pls_au_mgL=pls_au_mgL,
            pond_freeboard_m=0.8,
            created_by=contractor_id,
        )
        db.add(log)
        logs.append(log)
        print(f"Created DailyControlLog for {log_date}")
    
    db.commit()
    return logs


def create_weekly_summary(db: Session, heap_config_id: str, manager_id: str, week_start: date, cn_used_kg: float, heap_config: HeapConfig):
    """Create WeeklyControlSummary."""
    week_end = week_start + timedelta(days=6)
    
    existing = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config_id,
        WeeklyControlSummary.week_start_date == week_start
    ).first()
    if existing:
        print(f"WeeklyControlSummary for {week_start} already exists")
        return existing
    
    daily_logs = db.query(DailyControlLog).filter(
        DailyControlLog.heap_config_id == heap_config_id,
        DailyControlLog.log_date >= week_start,
        DailyControlLog.log_date <= week_end
    ).all()
    
    weekly_solution_applied_m3 = sum(log.flow_m3_per_hr * log.irrigation_hours for log in daily_logs)
    weekly_pls_flow_m3 = sum(log.pls_flow_m3 for log in daily_logs)
    weekly_gold_in_pls_g = sum(log.pls_au_mgL * log.pls_flow_m3 for log in daily_logs)
    
    previous_summaries = db.query(WeeklyControlSummary).filter(
        WeeklyControlSummary.heap_config_id == heap_config_id,
        WeeklyControlSummary.week_start_date < week_start
    ).all()
    previous_gold = sum(s.weekly_gold_in_pls_g for s in previous_summaries)
    cumulative_gold_in_pls_g = previous_gold + weekly_gold_in_pls_g
    
    contained_gold_g = heap_config.heap_tonnage_t * heap_config.head_grade_gpt
    recovery_pct = (cumulative_gold_in_pls_g / contained_gold_g) * 100 if contained_gold_g > 0 else None
    cn_consumption_kgpt = cn_used_kg / heap_config.heap_tonnage_t
    cn_efficiency_gpkg = cumulative_gold_in_pls_g / cn_used_kg if cn_used_kg > 0 else None
    
    summary = WeeklyControlSummary(
        id=str(uuid4()),
        heap_config_id=heap_config_id,
        week_start_date=week_start,
        week_end_date=week_end,
        cn_used_kg=cn_used_kg,
        weekly_solution_applied_m3=weekly_solution_applied_m3,
        weekly_pls_flow_m3=weekly_pls_flow_m3,
        weekly_gold_in_pls_g=weekly_gold_in_pls_g,
        cumulative_gold_in_pls_g=cumulative_gold_in_pls_g,
        contained_gold_g=contained_gold_g,
        recovery_pct=recovery_pct,
        cn_consumption_kgpt=cn_consumption_kgpt,
        cn_efficiency_gpkg=cn_efficiency_gpkg,
        created_by=manager_id,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    print(f"Created WeeklyControlSummary for {week_start}")
    return summary


def create_stop_decision(db: Session, heap_config_id: str, weekly_summary_id: str, manager_id: str, weekly_summary: WeeklyControlSummary, benchmark: BenchmarkConfig):
    """Create StopLeachDecision."""
    existing = db.query(StopLeachDecision).filter(
        StopLeachDecision.weekly_summary_id == weekly_summary_id
    ).first()
    if existing:
        print(f"StopLeachDecision for weekly summary already exists")
        return existing
    
    decision_reasons = []
    stop_recommendation = 0
    
    if weekly_summary.cn_efficiency_gpkg and weekly_summary.cn_efficiency_gpkg < benchmark.cn_efficiency_min_gpkg:
        decision_reasons.append(f"Cyanide efficiency ({weekly_summary.cn_efficiency_gpkg:.4f} g/kg) below minimum ({benchmark.cn_efficiency_min_gpkg} g/kg)")
        stop_recommendation = 1
    
    if weekly_summary.cn_consumption_kgpt and weekly_summary.cn_consumption_kgpt > benchmark.cn_consumption_max_kgpt:
        decision_reasons.append(f"Cyanide consumption ({weekly_summary.cn_consumption_kgpt:.4f} kg/t) above maximum ({benchmark.cn_consumption_max_kgpt} kg/t)")
        stop_recommendation = 1
    
    if not decision_reasons:
        decision_reasons.append("All metrics within acceptable ranges - continue leaching")
    
    system_status = "STOP" if stop_recommendation == 1 else "CONTINUE"
    
    decision = StopLeachDecision(
        id=str(uuid4()),
        heap_config_id=heap_config_id,
        weekly_summary_id=weekly_summary_id,
        decision_date=weekly_summary.week_end_date,
        stop_recommendation=stop_recommendation,
        recovery_pct=weekly_summary.recovery_pct,
        cn_efficiency_gpkg=weekly_summary.cn_efficiency_gpkg,
        cn_consumption_kgpt=weekly_summary.cn_consumption_kgpt,
        cumulative_gold_in_pls_g=weekly_summary.cumulative_gold_in_pls_g,
        decision_reasons=decision_reasons,
        system_status=system_status,
        created_by=manager_id,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    print(f"Created StopLeachDecision: {system_status}")
    return decision


def create_override(db: Session, heap_config_id: str, decision_id: str, manager_id: str, decision: StopLeachDecision):
    """Create StopLeachOverride."""
    if decision.stop_recommendation != 1:
        print("No override needed - decision is CONTINUE")
        return None
    
    existing = db.query(StopLeachOverride).filter(
        StopLeachOverride.decision_id == decision_id
    ).first()
    if existing:
        print("StopLeachOverride already exists")
        return existing
    
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
    
    override = StopLeachOverride(
        id=str(uuid4()),
        heap_config_id=heap_config_id,
        decision_id=decision_id,
        override_action="CONTINUE",
        override_reason="TRIAL_TEST_CONTINUATION",
        override_justification_text="Management has reviewed the economic metrics and determined that continued leaching is warranted for trial evaluation purposes. Recovery patterns will be monitored closely over the next monitoring period.",
        decision_snapshot=decision_snapshot,
        override_by=manager_id,
    )
    db.add(override)
    
    decision.system_status = "CONTINUE_UNDER_OVERRIDE"
    
    db.commit()
    db.refresh(override)
    print("Created StopLeachOverride: CONTINUE_UNDER_OVERRIDE")
    return override


def seed_all():
    """Seed all demo data."""
    print("=" * 60)
    print("SEEDING DEMO DATA FOR HEAP LEACHING MODULE")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        print("\n1. Creating demo users...")
        users = create_demo_users(db)
        
        print("\n2. Creating HeapConfig...")
        heap_config = create_heap_config(db, users["manager"].id)
        
        print("\n3. Creating BenchmarkConfig...")
        benchmark = create_benchmark_config(db, heap_config.id, users["admin"].id)
        
        print("\n4. Creating Week 1 DailyControlLogs (normal scenario)...")
        create_daily_logs(db, heap_config.id, users["contractor"].id, date(2025, 1, 1), 7, "normal")
        
        print("\n5. Creating Week 1 WeeklyControlSummary...")
        week1_summary = create_weekly_summary(db, heap_config.id, users["manager"].id, date(2025, 1, 1), 800.0, heap_config)
        
        print("\n6. Creating Week 1 StopLeachDecision...")
        week1_decision = create_stop_decision(db, heap_config.id, week1_summary.id, users["manager"].id, week1_summary, benchmark)
        
        print("\n7. Creating Week 2 DailyControlLogs (low gold scenario)...")
        create_daily_logs(db, heap_config.id, users["contractor"].id, date(2025, 1, 8), 7, "low_gold")
        
        print("\n8. Creating Week 2 WeeklyControlSummary (high CN consumption)...")
        week2_summary = create_weekly_summary(db, heap_config.id, users["manager"].id, date(2025, 1, 8), 2500.0, heap_config)
        
        print("\n9. Creating Week 2 StopLeachDecision...")
        week2_decision = create_stop_decision(db, heap_config.id, week2_summary.id, users["manager"].id, week2_summary, benchmark)
        
        print("\n10. Creating Management Override for Week 2...")
        create_override(db, heap_config.id, week2_decision.id, users["manager"].id, week2_decision)
        
        print("\n" + "=" * 60)
        print("DEMO DATA SEEDING COMPLETE")
        print("=" * 60)
        print("\nDemo Credentials:")
        print("-" * 40)
        print("Contractor: contractor_demo@klusetic.com / demo123")
        print("Engineer:   engineer_demo@klusetic.com / demo123")
        print("Manager:    manager_demo@klusetic.com / demo123")
        print("Admin:      admin_demo@klusetic.com / admin123")
        print("-" * 40)
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
