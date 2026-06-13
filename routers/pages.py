from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import database as models
from config import templates
from dependencies import get_db

router = APIRouter()

WHISKEY_TYPES = [
    "Single Malt Scotch",
    "Blended Scotch",
    "Blended Malt Scotch",
    "Single Grain Scotch",
    "Bourbon",
    "Tennessee Whiskey",
    "Rye Whiskey",
    "Irish Whiskey",
    "Japanese Whisky",
    "Canadian Whisky",
    "World Whisky",
]

REGIONS = [
    "Speyside", "Highlands", "Islay", "Lowlands", "Campbeltown", "Islands",
    "Kentucky", "Tennessee", "Ireland", "Japan", "Canada", "Other",
]


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {
        "request": request,
        "user": request.state.user,
    })


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    total = db.query(models.Bottle).filter(models.Bottle.is_deleted == False).count()
    sealed = db.query(models.Bottle).filter(models.Bottle.is_deleted == False, models.Bottle.status == "sealed").count()
    opened = db.query(models.Bottle).filter(models.Bottle.is_deleted == False, models.Bottle.status == "opened").count()
    finished = db.query(models.Bottle).filter(models.Bottle.is_deleted == False, models.Bottle.status == "finished").count()
    wishlist_count = db.query(models.Wishlist).count()
    liked = db.query(models.Bottle).filter(models.Bottle.is_deleted == False, models.Bottle.liked == True).count()
    buy_again = db.query(models.Bottle).filter(models.Bottle.is_deleted == False, models.Bottle.buy_again == True).count()
    recent = (
        db.query(models.Bottle)
        .filter(models.Bottle.is_deleted == False)
        .order_by(models.Bottle.id.desc())
        .limit(6)
        .all()
    )
    # Type breakdown
    type_counts = {}
    for wt in WHISKEY_TYPES:
        c = db.query(models.Bottle).filter(
            models.Bottle.is_deleted == False, models.Bottle.whiskey_type == wt
        ).count()
        if c > 0:
            type_counts[wt] = c

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": request.state.user,
        "total": total,
        "sealed": sealed,
        "opened": opened,
        "finished": finished,
        "wishlist_count": wishlist_count,
        "liked": liked,
        "buy_again": buy_again,
        "recent": recent,
        "type_counts": type_counts,
    })


@router.get("/inventory", response_class=HTMLResponse)
async def inventory_page(request: Request, db: Session = Depends(get_db)):
    bottles = (
        db.query(models.Bottle)
        .filter(models.Bottle.is_deleted == False)
        .order_by(models.Bottle.brand, models.Bottle.name)
        .all()
    )
    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "user": request.state.user,
        "bottles": bottles,
        "whiskey_types": WHISKEY_TYPES,
        "regions": REGIONS,
    })


@router.get("/bottle/{bottle_id}", response_class=HTMLResponse)
async def bottle_detail_page(bottle_id: int, request: Request, db: Session = Depends(get_db)):
    bottle = db.query(models.Bottle).filter(models.Bottle.id == bottle_id).first()
    if not bottle:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/inventory", status_code=302)
    tastings = (
        db.query(models.Tasting)
        .filter(models.Tasting.bottle_id == bottle_id)
        .order_by(models.Tasting.date_tasted.desc())
        .all()
    )
    return templates.TemplateResponse("bottle_detail.html", {
        "request": request,
        "user": request.state.user,
        "bottle": bottle,
        "tastings": tastings,
        "whiskey_types": WHISKEY_TYPES,
        "regions": REGIONS,
    })


@router.get("/wishlist", response_class=HTMLResponse)
async def wishlist_page(request: Request, db: Session = Depends(get_db)):
    items = db.query(models.Wishlist).order_by(models.Wishlist.id.desc()).all()
    return templates.TemplateResponse("wishlist.html", {
        "request": request,
        "user": request.state.user,
        "items": items,
        "whiskey_types": WHISKEY_TYPES,
        "regions": REGIONS,
    })


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request, db: Session = Depends(get_db)):
    if not getattr(request.state, "user", None) or not request.state.user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(403, "Admin required")
    users = db.query(models.User).order_by(models.User.id).all()
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user": request.state.user,
        "users": users,
    })


@router.get("/admin/trash", response_class=HTMLResponse)
async def trash_page(request: Request, db: Session = Depends(get_db)):
    if not getattr(request.state, "user", None) or not request.state.user.is_admin:
        from fastapi import HTTPException
        raise HTTPException(403, "Admin required")
    return templates.TemplateResponse("admin_trash.html", {
        "request": request,
        "user": request.state.user,
    })
