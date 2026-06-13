from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db, save_uploaded_file
from schemas import BottlePatchPayload, SoldPayload
from whiskey_kb import save_correction as kb_save_correction  # [KB]

router = APIRouter(prefix="/bottles", tags=["bottles"])


def _bottle_dict(b: models.Bottle) -> dict:
    return {
        "id": b.id,
        "brand": b.brand,
        "name": b.name,
        "whiskey_type": b.whiskey_type,
        "region": b.region,
        "country": b.country,
        "age_statement": b.age_statement,
        "vintage_year": b.vintage_year,
        "abv": b.abv,
        "volume_ml": b.volume_ml,
        "price_paid": b.price_paid,
        "date_acquired": b.date_acquired,
        "upc": b.upc,
        "status": b.status,
        "image_path_1": b.image_path_1,
        "image_path_2": b.image_path_2,
        "notes": b.notes,
        "liked": b.liked,
        "buy_again": b.buy_again,
        "rating": b.rating,
        "is_deleted": b.is_deleted,
        "is_sold": b.is_sold,
        "price_sold": b.price_sold,
        "is_gift": b.is_gift,
        "is_collectible": b.is_collectible,
    }


@router.get("/")
def list_bottles(
    db: Session = Depends(get_db),
    whiskey_type: Optional[str] = None,
    status: Optional[str] = None,
    region: Optional[str] = None,
    liked: Optional[bool] = None,
    buy_again: Optional[bool] = None,
):
    q = db.query(models.Bottle).filter(models.Bottle.is_deleted == False)
    if whiskey_type:
        q = q.filter(models.Bottle.whiskey_type == whiskey_type)
    if status:
        q = q.filter(models.Bottle.status == status)
    if region:
        q = q.filter(models.Bottle.region == region)
    if liked is not None:
        q = q.filter(models.Bottle.liked == liked)
    if buy_again is not None:
        q = q.filter(models.Bottle.buy_again == buy_again)
    return [_bottle_dict(b) for b in q.order_by(models.Bottle.brand, models.Bottle.name).all()]


@router.post("/")
async def add_bottle(
    request: Request,
    brand: str = Form(...),
    name: Optional[str] = Form(default=None),
    whiskey_type: Optional[str] = Form(default=None),
    region: Optional[str] = Form(default=None),
    country: Optional[str] = Form(default=None),
    age_statement: Optional[int] = Form(default=None),
    vintage_year: Optional[int] = Form(default=None),
    abv: Optional[float] = Form(default=None),
    volume_ml: Optional[int] = Form(default=750),
    price_paid: Optional[float] = Form(default=None),
    date_acquired: Optional[str] = Form(default=None),
    upc: Optional[str] = Form(default=None),
    status: str = Form(default="sealed"),
    notes: Optional[str] = Form(default=None),
    is_gift: Optional[bool] = Form(default=False),
    is_collectible: Optional[bool] = Form(default=False),
    image: Optional[UploadFile] = File(default=None),
    existing_image_path: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    if image and getattr(image, "filename", None):
        img_path = await save_uploaded_file(image, "bottle")
    elif existing_image_path:
        img_path = existing_image_path
    else:
        img_path = None
    b = models.Bottle(
        brand=brand.strip(),
        name=name.strip() if name else None,
        whiskey_type=whiskey_type or None,
        region=region or None,
        country=country or None,
        age_statement=age_statement,
        vintage_year=vintage_year,
        abv=abv,
        volume_ml=volume_ml or 750,
        price_paid=price_paid,
        date_acquired=date_acquired or datetime.utcnow().strftime("%Y-%m-%d"),
        upc=upc or None,
        status=status or "sealed",
        notes=notes or None,
        is_gift=bool(is_gift),
        is_collectible=bool(is_collectible),
        image_path_1=img_path,
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return _bottle_dict(b)


@router.get("/{bottle_id}")
def get_bottle(bottle_id: int, db: Session = Depends(get_db)):
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    return _bottle_dict(b)


@router.patch("/{bottle_id}")
def patch_bottle(bottle_id: int, payload: BottlePatchPayload, db: Session = Depends(get_db)):
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(b, field, value)
    db.commit()
    db.refresh(b)
    # [KB] Learn from user corrections to enrichable fields
    kb_fields = {f: updates[f] for f in ("whiskey_type", "region", "country", "abv") if f in updates}
    if kb_fields:
        kb_save_correction(b.brand, kb_fields)
    return _bottle_dict(b)


@router.post("/{bottle_id}/update-photo/")
async def update_photo(
    bottle_id: int,
    slot: int = Form(default=1),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    path = await save_uploaded_file(image, "bottle")
    if slot == 2:
        b.image_path_2 = path
    else:
        b.image_path_1 = path
    db.commit()
    return {"image_path_1": b.image_path_1, "image_path_2": b.image_path_2}


@router.post("/{bottle_id}/swap-photos/")
def swap_photos(bottle_id: int, db: Session = Depends(get_db)):
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    b.image_path_1, b.image_path_2 = b.image_path_2, b.image_path_1
    db.commit()
    return {"image_path_1": b.image_path_1, "image_path_2": b.image_path_2}


@router.post("/{bottle_id}/status/")
def set_status(bottle_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    if status not in ("sealed", "opened", "finished"):
        raise HTTPException(400, "Invalid status")
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    b.status = status
    db.commit()
    return _bottle_dict(b)


@router.post("/{bottle_id}/sell/")
def sell_bottle(bottle_id: int, payload: SoldPayload, db: Session = Depends(get_db)):
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    b.is_sold = True
    b.price_sold = payload.price_sold
    db.commit()
    return _bottle_dict(b)


@router.post("/{bottle_id}/trash/")
def trash_bottle(bottle_id: int, request: Request, db: Session = Depends(get_db)):
    if not getattr(request.state, "user", None):
        raise HTTPException(401)
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    b.is_deleted = True
    db.commit()
    return {"ok": True}


@router.post("/{bottle_id}/restore/")
def restore_bottle(bottle_id: int, request: Request, db: Session = Depends(get_db)):
    if not getattr(request.state, "user", None) or not request.state.user.is_admin:
        raise HTTPException(403, "Admin required")
    b = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not b:
        raise HTTPException(404, "Not found")
    b.is_deleted = False
    db.commit()
    return {"ok": True}
