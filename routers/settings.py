from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db
from schemas import SettingsPatch

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def get_settings(db: Session = Depends(get_db)):
    return {s.key: s.value for s in db.query(models.Setting).all()}


@router.patch("/{key}")
def update_setting(key: str, payload: SettingsPatch, request: Request, db: Session = Depends(get_db)):
    if not getattr(request.state, "user", None) or not request.state.user.is_admin:
        raise HTTPException(403, "Admin required")
    s = db.query(models.Setting).filter(models.Setting.key == key).first()
    if not s:
        s = models.Setting(key=key, value=payload.value)
        db.add(s)
    else:
        s.value = payload.value
    db.commit()
    return {"key": key, "value": payload.value}
