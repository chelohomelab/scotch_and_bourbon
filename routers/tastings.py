from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db
from schemas import TastingPayload

router = APIRouter(prefix="/tastings", tags=["tastings"])


def _tasting_dict(t: models.Tasting) -> dict:
    return {
        "id": t.id,
        "bottle_id": t.bottle_id,
        "date_tasted": t.date_tasted,
        "rating": t.rating,
        "liked": t.liked,
        "buy_again": t.buy_again,
        "nose": t.nose,
        "palate": t.palate,
        "finish": t.finish,
        "overall": t.overall,
    }


@router.get("/bottle/{bottle_id}")
def get_tastings(bottle_id: int, db: Session = Depends(get_db)):
    tastings = (
        db.query(models.Tasting)
        .filter(models.Tasting.bottle_id == bottle_id)
        .order_by(models.Tasting.date_tasted.desc())
        .all()
    )
    return [_tasting_dict(t) for t in tastings]


@router.post("/bottle/{bottle_id}")
def add_tasting(bottle_id: int, payload: TastingPayload, db: Session = Depends(get_db)):
    bottle = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not bottle:
        raise HTTPException(404, "Bottle not found")

    t = models.Tasting(
        bottle_id=bottle_id,
        date_tasted=payload.date_tasted or datetime.utcnow().strftime("%Y-%m-%d"),
        rating=payload.rating,
        liked=payload.liked,
        buy_again=payload.buy_again,
        nose=payload.nose,
        palate=payload.palate,
        finish=payload.finish,
        overall=payload.overall,
    )
    db.add(t)

    # Sync bottle-level fields from latest tasting
    if payload.liked is not None:
        bottle.liked = payload.liked
    if payload.buy_again is not None:
        bottle.buy_again = payload.buy_again
    if payload.rating is not None:
        bottle.rating = payload.rating

    db.commit()
    db.refresh(t)
    return _tasting_dict(t)


@router.patch("/{tasting_id}")
def update_tasting(tasting_id: int, payload: TastingPayload, db: Session = Depends(get_db)):
    t = db.query(models.Tasting).filter(models.Tasting.id == tasting_id).first()
    if not t:
        raise HTTPException(404, "Not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return _tasting_dict(t)


@router.delete("/{tasting_id}")
def delete_tasting(tasting_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Tasting).filter(models.Tasting.id == tasting_id).first()
    if not t:
        raise HTTPException(404, "Not found")
    db.delete(t)
    db.commit()
    return {"deleted": tasting_id}
