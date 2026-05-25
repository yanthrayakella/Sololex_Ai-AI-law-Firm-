from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth_utils import get_current_user
from db import Alert, User, get_db
from schemas import AlertItem

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertItem])
def list_alerts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Alert)
        .filter(Alert.user_id == user.id)
        .order_by(Alert.created_at.desc())
        .limit(200)
        .all()
    )
    return rows


@router.put("/{alert_id}/read", response_model=AlertItem)
def mark_read(alert_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert = (
        db.query(Alert)
        .filter(Alert.id == alert_id, Alert.user_id == user.id)
        .first()
    )
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert
