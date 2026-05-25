from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth_utils import get_current_user
from db import User, get_db
from schemas import UserProfile, UserUpdateBody

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/profile", response_model=UserProfile)
def profile(user: User = Depends(get_current_user)):
    return user


@router.put("/profile", response_model=UserProfile)
def update_profile(body: UserUpdateBody, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.name is not None:
        user.name = body.name
    if body.company is not None:
        user.company = body.company
    if body.wechat_openid is not None:
        user.wechat_openid = body.wechat_openid
    db.commit()
    db.refresh(user)
    return user
