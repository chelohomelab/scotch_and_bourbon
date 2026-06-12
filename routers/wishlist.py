from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db, save_uploaded_file
from schemas import WishlistPatchPayload

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


def _wish_dict(w: models.Wishlist) -> dict:
    return {
        "id": w.id,
        "brand": w.brand,
        "name": w.name,
        "whiskey_type": w.whiskey_type,
        "region": w.region,
        "priority": w.priority,
        "est_price": w.est_price,
        "url": w.url,
        "notes": w.notes,
        "image_path": w.image_path,
        "created_at": w.created_at,
    }


@router.get("/")
def list_wishlist(db: Session = Depends(get_db)):
    return [_wish_dict(w) for w in db.query(models.Wishlist).order_by(models.Wishlist.id.desc()).all()]


@router.post("/")
async def add_wishlist(
    brand: str = Form(...),
    name: Optional[str] = Form(default=None),
    whiskey_type: Optional[str] = Form(default=None),
    region: Optional[str] = Form(default=None),
    priority: str = Form(default="Medium"),
    est_price: Optional[float] = Form(default=None),
    url: Optional[str] = Form(default=None),
    notes: Optional[str] = Form(default=None),
    image: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
):
    img_path = await save_uploaded_file(image, "wish")
    w = models.Wishlist(
        brand=brand.strip(),
        name=name.strip() if name else None,
        whiskey_type=whiskey_type or None,
        region=region or None,
        priority=priority or "Medium",
        est_price=est_price,
        url=url or None,
        notes=notes or None,
        image_path=img_path,
        created_at=datetime.utcnow().strftime("%Y-%m-%d"),
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return _wish_dict(w)


@router.patch("/{wish_id}")
def patch_wishlist(wish_id: int, payload: WishlistPatchPayload, db: Session = Depends(get_db)):
    w = db.query(models.Wishlist).filter(models.Wishlist.id == wish_id).first()
    if not w:
        raise HTTPException(404, "Not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(w, field, value)
    db.commit()
    db.refresh(w)
    return _wish_dict(w)


@router.post("/{wish_id}/update-photo/")
async def update_photo(wish_id: int, image: UploadFile = File(...), db: Session = Depends(get_db)):
    w = db.query(models.Wishlist).filter(models.Wishlist.id == wish_id).first()
    if not w:
        raise HTTPException(404, "Not found")
    w.image_path = await save_uploaded_file(image, "wish")
    db.commit()
    return _wish_dict(w)


@router.delete("/{wish_id}")
def delete_wishlist(wish_id: int, db: Session = Depends(get_db)):
    w = db.query(models.Wishlist).filter(models.Wishlist.id == wish_id).first()
    if not w:
        raise HTTPException(404, "Not found")
    db.delete(w)
    db.commit()
    return {"deleted": wish_id}


@router.post("/{wish_id}/convert/")
def convert_wishlist(wish_id: int, db: Session = Depends(get_db)):
    w = db.query(models.Wishlist).filter(models.Wishlist.id == wish_id).first()
    if not w:
        raise HTTPException(404, "Not found")
    b = models.Bottle(
        brand=w.brand or "Unknown",
        name=w.name,
        whiskey_type=w.whiskey_type,
        region=w.region,
        price_paid=w.est_price,
        status="sealed",
        image_path_1=w.image_path,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    db.delete(w)
    db.commit()
    return {"id": b.id}
