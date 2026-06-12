from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db, _hash_pw
from schemas import AdminUserPatch

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(request: Request):
    if not getattr(request.state, "user", None) or not request.state.user.is_admin:
        raise HTTPException(403, "Admin required")


@router.get("/trash-items")
def trash_items(request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    bottles = db.query(models.Bottle).filter(models.Bottle.is_deleted == True).all()
    return {
        "bottles": [
            {
                "id": b.id,
                "label": f"{b.brand} {b.name or ''}".strip(),
                "whiskey_type": b.whiskey_type,
                "image": b.image_path_1,
            }
            for b in bottles
        ]
    }


@router.delete("/trash/bottles/{bottle_id}")
def perma_delete_bottle(bottle_id: int, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id, models.Bottle.is_deleted == True).first()
    if not b:
        raise HTTPException(404, "Not found in trash")
    db.delete(b)
    db.commit()
    return {"deleted": bottle_id}


@router.patch("/users/{user_id}")
def patch_user(user_id: int, payload: AdminUserPatch, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Not found")
    if payload.is_admin is not None:
        u.is_admin = payload.is_admin
    if payload.is_active is not None:
        u.is_active = payload.is_active
    db.commit()
    return {"id": u.id, "username": u.username, "is_admin": u.is_admin, "is_active": u.is_active}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    if user_id == request.state.user.id:
        raise HTTPException(400, "Cannot delete your own account")
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(404, "Not found")
    db.delete(u)
    db.commit()
    return {"deleted": user_id}


@router.post("/users/")
async def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(default=None),
    is_admin: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(request)
    if db.query(models.User).filter(models.User.username == username.strip()).first():
        raise HTTPException(400, "Username already exists")
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    u = models.User(
        username=username.strip(),
        email=email.strip() if email else None,
        hashed_password=_hash_pw(password),
        is_admin=bool(is_admin),
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "username": u.username, "is_admin": u.is_admin}
