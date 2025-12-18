"""
Test configuration and fixtures for Heap Leaching module E2E tests.
"""

import pytest
import os
import sys
from datetime import date, datetime, timedelta
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
import models
from auth import get_password_hash


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = models.User(
        id=str(uuid4()),
        name="Admin User",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    user = models.User(
        id=str(uuid4()),
        name="Manager User",
        email="manager@test.com",
        hashed_password=get_password_hash("manager123"),
        role="manager",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def engineer_user(db):
    """Create an engineer user."""
    user = models.User(
        id=str(uuid4()),
        name="Engineer User",
        email="engineer@test.com",
        hashed_password=get_password_hash("engineer123"),
        role="supervisor",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def contractor_user(db):
    """Create a contractor user."""
    user = models.User(
        id=str(uuid4()),
        name="Contractor User",
        email="contractor@test.com",
        hashed_password=get_password_hash("contractor123"),
        role="operator",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_auth_token(client, email: str, password: str) -> str:
    """Get authentication token for a user."""
    response = client.post(
        "/token",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    """Get admin authentication token."""
    return get_auth_token(client, "admin@test.com", "admin123")


@pytest.fixture
def manager_token(client, manager_user):
    """Get manager authentication token."""
    return get_auth_token(client, "manager@test.com", "manager123")


@pytest.fixture
def engineer_token(client, engineer_user):
    """Get engineer authentication token."""
    return get_auth_token(client, "engineer@test.com", "engineer123")


@pytest.fixture
def contractor_token(client, contractor_user):
    """Get contractor authentication token."""
    return get_auth_token(client, "contractor@test.com", "contractor123")


@pytest.fixture
def heap_config_data():
    """Standard HeapConfig test data."""
    return {
        "heap_id": "HEAP-001",
        "heap_tonnage_t": 1000.0,
        "head_grade_gpt": 2.0,
        "leach_start_date": "2025-01-01",
    }


@pytest.fixture
def benchmark_config_data():
    """Standard BenchmarkConfig test data (oxide defaults)."""
    return {
        "application_rate_min_L_m2_hr": 8.0,
        "application_rate_max_L_m2_hr": 12.0,
        "cn_min_ppm": 200.0,
        "cn_max_ppm": 500.0,
        "ph_min": 10.5,
        "ph_max": 11.0,
        "pls_return_min_pct": 80.0,
        "pond_freeboard_min_m": 0.5,
        "cn_consumption_max_kgpt": 2.0,
        "cn_efficiency_min_gpkg": 0.5,
        "pls_low_au_mgL": 0.2,
    }


@pytest.fixture
def valid_daily_log_data():
    """Valid DailyControlLog data that passes all rules."""
    return {
        "log_date": "2025-01-01",
        "area_irrigated_m2": 1000.0,
        "flow_m3_per_hr": 10.0,
        "irrigation_hours": 20.0,
        "applied_cn_ppm": 300.0,
        "applied_ph": 10.8,
        "pls_flow_m3": 180.0,
        "pls_au_mgL": 0.5,
        "pond_freeboard_m": 0.8,
    }


@pytest.fixture
def setup_heap_and_benchmark(client, admin_token, manager_token, heap_config_data, benchmark_config_data):
    """Create HeapConfig and BenchmarkConfig for testing."""
    headers_manager = {"Authorization": f"Bearer {manager_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    heap_response = client.post(
        "/api/v1/modules/heap-leaching/heap-config",
        json=heap_config_data,
        headers=headers_manager,
    )
    
    benchmark_response = client.post(
        "/api/v1/modules/heap-leaching/benchmark-config",
        json=benchmark_config_data,
        headers=headers_admin,
    )
    
    return {
        "heap_config": heap_response.json(),
        "benchmark_config": benchmark_response.json(),
    }
