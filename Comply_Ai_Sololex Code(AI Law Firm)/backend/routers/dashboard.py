from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth_utils import get_current_user
from db import Alert, Contract, User, get_db
from schemas import AlertItem, DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    contracts = db.query(Contract).filter(Contract.user_id == user.id).all()
    if not contracts:
        score = 100
    else:
        score = int(round(sum(c.risk_score or 0 for c in contracts) / len(contracts)))
    open_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.user_id == user.id, Alert.is_read.is_(False))
        .scalar()
        or 0
    )
    high = (
        db.query(func.count(Alert.id))
        .filter(Alert.user_id == user.id, Alert.severity == "HIGH", Alert.is_read.is_(False))
        .scalar()
        or 0
    )
    return DashboardStats(
        compliance_score=score,
        open_alerts=int(open_alerts),
        contracts_count=len(contracts),
        high_severity_count=int(high),
    )


@router.get("/alerts-preview", response_model=list[AlertItem])
def alerts_preview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Alert)
        .filter(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(8)
        .all()
    )
    return rows
