
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from auth import (
    authenticate_user, create_access_token, get_current_active_user,
    require_admin, require_supervisor_or_admin, require_manager_or_above,
    Token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)

from modules import register_module, list_modules
from modules.heap_leaching import MODULE_METADATA, router as heap_leaching_router
from modules.heap_leaching.models import (
    HeapConfig, HeapConfigHistory, BenchmarkConfig, BenchmarkChangeLog
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mine KPI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_module(MODULE_METADATA["module_id"], MODULE_METADATA)

app.include_router(heap_leaching_router, prefix="/api/v1/modules", tags=["Modules"])

class Role(str, Enum):
    operator = "operator"
    manager = "manager"
    supervisor = "supervisor"
    admin = "admin"

class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: Role

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool

class RecordCreate(BaseModel):
    module: str
    data: dict
    manager_on_duty: str

class RecordResponse(BaseModel):
    id: str
    module: str
    data: dict
    manager_on_duty: str
    submitted_by: str
    approval_status: str
    approved_by: Optional[str] = None
    timestamp: datetime

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        id=str(uuid4()),
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role.value
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        email=db_user.email,
        role=db_user.role,
        is_active=db_user.is_active
    )

@app.get("/users", response_model=List[UserResponse])
async def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_above)
):
    users = db.query(models.User).all()
    return [UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active
    ) for user in users]

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_active_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active
    )

@app.post("/record", response_model=RecordResponse)
async def submit_record(
    record_data: RecordCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_record = models.Record(
        id=str(uuid4()),
        module=record_data.module,
        data=record_data.data,
        manager_on_duty=record_data.manager_on_duty,
        submitted_by=current_user.id
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return RecordResponse(
        id=db_record.id,
        module=db_record.module,
        data=db_record.data,
        manager_on_duty=db_record.manager_on_duty,
        submitted_by=db_record.submitted_by,
        approval_status=db_record.approval_status,
        approved_by=db_record.approved_by,
        timestamp=db_record.timestamp
    )

@app.get("/records", response_model=List[RecordResponse])
async def get_all_records(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.role == "operator":
        records = db.query(models.Record).filter(models.Record.submitted_by == current_user.id).all()
    else:
        records = db.query(models.Record).all()
    
    return [RecordResponse(
        id=record.id,
        module=record.module,
        data=record.data,
        manager_on_duty=record.manager_on_duty,
        submitted_by=record.submitted_by,
        approval_status=record.approval_status,
        approved_by=record.approved_by,
        timestamp=record.timestamp
    ) for record in records]

@app.post("/record/{record_id}/approve")
async def approve_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_above)
):
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    record.approval_status = "approved"
    record.approved_by = current_user.id
    db.commit()
    
    return {"status": "approved"}

@app.post("/record/{record_id}/reject")
async def reject_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_manager_or_above)
):
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    record.approval_status = "rejected"
    record.approved_by = current_user.id
    db.commit()
    
    return {"status": "rejected"}

@app.get("/record/{record_id}", response_model=RecordResponse)
async def get_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    record = db.query(models.Record).filter(models.Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    if current_user.role == "operator" and record.submitted_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this record")
    
    return RecordResponse(
        id=record.id,
        module=record.module,
        data=record.data,
        manager_on_duty=record.manager_on_duty,
        submitted_by=record.submitted_by,
        approval_status=record.approval_status,
        approved_by=record.approved_by,
        timestamp=record.timestamp
    )


@app.get("/api/v1/modules", tags=["Modules"])
async def get_registered_modules():
    """List all registered modules in the platform."""
    return {
        "modules": list_modules(),
        "count": len(list_modules()),
    }
