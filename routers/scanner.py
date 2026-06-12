import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db, save_uploaded_file

router = APIRouter(prefix="/scanner", tags=["scanner"])


def _require_admin(request: Request):
    if not getattr(request.state, "user", None) or not request.state.user.is_admin:
        raise HTTPException(403, "Admin required")


def _entry_dict(e: models.ScannerEntry) -> dict:
    data = {}
    if e.data_json:
        try:
            data = json.loads(e.data_json)
        except Exception:
            pass
    return {
        "id": e.id,
        "upc": e.upc,
        "title": e.title,
        "brand": e.brand,
        "name": e.name,
        "whiskey_type": e.whiskey_type,
        "region": e.region,
        "age_statement": e.age_statement,
        "abv": e.abv,
        "volume_ml": e.volume_ml,
        "notes": e.notes,
        "image_path_1": e.image_path_1,
        "image_path_2": e.image_path_2,
        "image_path_3": e.image_path_3,
        "data": data,
        "created_at": e.created_at,
        "is_reviewed": e.is_reviewed,
    }


@router.get("/entries")
def list_entries(request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    return [_entry_dict(e) for e in db.query(models.ScannerEntry).order_by(models.ScannerEntry.id.desc()).all()]


@router.post("/entries")
async def create_entry(
    request: Request,
    upc: Optional[str] = Form(default=None),
    brand: Optional[str] = Form(default=None),
    name: Optional[str] = Form(default=None),
    whiskey_type: Optional[str] = Form(default=None),
    region: Optional[str] = Form(default=None),
    age_statement: Optional[int] = Form(default=None),
    abv: Optional[float] = Form(default=None),
    volume_ml: Optional[int] = Form(default=None),
    notes: Optional[str] = Form(default=None),
    photo: Optional[UploadFile] = File(default=None),
    db: Session = Depends(get_db),
):
    _require_admin(request)
    image_path = await save_uploaded_file(photo, "scan") if photo else None
    e = models.ScannerEntry(
        upc=upc or None,
        brand=brand or None,
        name=name or None,
        whiskey_type=whiskey_type or None,
        region=region or None,
        age_statement=age_statement,
        abv=abv,
        volume_ml=volume_ml,
        notes=notes or None,
        image_path_1=image_path,
        created_at=datetime.now(timezone.utc).date().isoformat(),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return _entry_dict(e)


@router.patch("/entries/{entry_id}")
async def update_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    e = db.query(models.ScannerEntry).filter(models.ScannerEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    body = await request.json()
    for field in ("upc", "brand", "name", "whiskey_type", "region", "age_statement",
                  "abv", "volume_ml", "notes", "data_json", "is_reviewed"):
        if field in body:
            setattr(e, field, body[field])
    db.commit()
    return _entry_dict(e)


@router.post("/entries/{entry_id}/add-photo")
async def add_photo(entry_id: int, request: Request, photo: UploadFile = File(...), db: Session = Depends(get_db)):
    _require_admin(request)
    e = db.query(models.ScannerEntry).filter(models.ScannerEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    path = await save_uploaded_file(photo, "scan")
    if not path:
        raise HTTPException(400, "Upload failed")
    if not e.image_path_1:
        e.image_path_1 = path
    elif not e.image_path_2:
        e.image_path_2 = path
    elif not e.image_path_3:
        e.image_path_3 = path
    else:
        raise HTTPException(400, "Max 3 photos per entry")
    db.commit()
    return {"image_path_1": e.image_path_1, "image_path_2": e.image_path_2, "image_path_3": e.image_path_3}


@router.delete("/entries/{entry_id}/photos/{slot}")
def delete_photo(entry_id: int, slot: int, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    e = db.query(models.ScannerEntry).filter(models.ScannerEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    if slot == 1:   e.image_path_1 = None
    elif slot == 2: e.image_path_2 = None
    elif slot == 3: e.image_path_3 = None
    db.commit()
    return {"ok": True}


@router.delete("/entries/reviewed")
def delete_reviewed(request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    count = db.query(models.ScannerEntry).filter(models.ScannerEntry.is_reviewed == True).delete()
    db.commit()
    return {"deleted": count}


@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    e = db.query(models.ScannerEntry).filter(models.ScannerEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    db.delete(e)
    db.commit()
    return {"deleted": entry_id}


@router.post("/entries/{entry_id}/autofill")
def autofill_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    _require_admin(request)
    e = db.query(models.ScannerEntry).filter(models.ScannerEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    if not e.upc:
        raise HTTPException(400, "No UPC on this entry")

    from routers.barcode import (
        _lookup_upcitemdb, _lookup_openfoodfacts,
        _parse_whiskey_type, _parse_age, _parse_abv, _parse_volume,
        _parse_region, _parse_brand, _parse_country, _download_upc_image,
        upsert_upc_cache,
    )
    import html

    upc = e.upc
    cached = db.query(models.UpcCache).filter(models.UpcCache.upc == upc).first()
    if cached:
        from routers.barcode import _cache_to_response
        info = _cache_to_response(cached)
    else:
        item = _lookup_upcitemdb(upc)
        if item:
            title = item.get("title") or item.get("description") or ""
            raw_brand = html.unescape(item.get("brand") or "")
            api_images = item.get("images") or []
        else:
            off = _lookup_openfoodfacts(upc)
            if off:
                title = off.get("product_name") or ""
                raw_brand = off.get("brands") or ""
                api_images = [off.get("image_url")] if off.get("image_url") else []
            else:
                raise HTTPException(404, "UPC not found in any external database")

        whiskey_type = _parse_whiskey_type(title)
        brand = _parse_brand(raw_brand, title)
        image_path = None
        for img_url in api_images:
            if img_url:
                image_path = _download_upc_image(upc, img_url)
                if image_path:
                    break

        info = {
            "brand": brand, "whiskey_type": whiskey_type, "region": _parse_region(title),
            "country": _parse_country(title, whiskey_type),
            "age_statement": _parse_age(title), "abv": _parse_abv(title),
            "volume_ml": _parse_volume(title), "image_path": image_path, "title": title,
        }
        upsert_upc_cache(db, upc, title=title, brand=brand, whiskey_type=whiskey_type,
                         region=info["region"], country=info["country"],
                         age_statement=info["age_statement"], abv=info["abv"],
                         volume_ml=info["volume_ml"], image_path=image_path)

    proposed = {}
    for field in ("brand", "whiskey_type", "region", "age_statement", "abv", "volume_ml"):
        val = info.get(field)
        if val is not None and not getattr(e, field, None):
            proposed[field] = val
    if info.get("image_path") and not e.image_path_1:
        proposed["image_path_1"] = info["image_path"]

    return {"proposed": proposed, "source": info.get("source", "api")}


@router.post("/entries/{entry_id}/commit")
def commit_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    """Convert a scanner entry into an actual bottle record."""
    _require_admin(request)
    e = db.query(models.ScannerEntry).filter(models.ScannerEntry.id == entry_id).first()
    if not e:
        raise HTTPException(404, "Not found")
    if not e.brand:
        raise HTTPException(400, "Brand is required before committing")

    b = models.Bottle(
        brand=e.brand,
        name=e.name,
        whiskey_type=e.whiskey_type,
        region=e.region,
        age_statement=e.age_statement,
        abv=e.abv,
        volume_ml=e.volume_ml or 750,
        upc=e.upc,
        status="sealed",
        notes=e.notes,
        image_path_1=e.image_path_1,
        image_path_2=e.image_path_2,
    )
    db.add(b)
    e.is_reviewed = True
    db.commit()
    db.refresh(b)
    return {"bottle_id": b.id}
