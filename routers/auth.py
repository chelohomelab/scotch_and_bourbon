import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

import database as models
from config import templates
from dependencies import get_db, _hash_pw, _verify_pw

router = APIRouter()


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request, db: Session = Depends(get_db)):
    if db.query(models.User).count() > 0:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("setup.html", {"request": request})


@router.post("/setup")
async def setup_submit(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(models.User).count() > 0:
        return RedirectResponse("/login", status_code=302)
    if len(password) < 8:
        return RedirectResponse("/setup?error=Password+must+be+at+least+8+characters", status_code=302)
    u = models.User(
        username=username.strip(),
        hashed_password=_hash_pw(password),
        is_admin=True,
        is_active=True,
    )
    db.add(u)
    db.commit()
    return RedirectResponse("/login", status_code=302)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    if db.query(models.User).count() == 0:
        return RedirectResponse("/setup", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    remember: str = Form(default=None),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(
        models.User.username == username.strip(),
        models.User.is_active == True,
    ).first()
    if not user or not _verify_pw(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid username or password"}, status_code=401
        )
    days = 30 if remember else 1
    session_id = uuid.uuid4().hex
    exp = datetime.now(timezone.utc) + timedelta(days=days)
    sess = models.UserSession(id=session_id, user_id=user.id, expires_at=exp.isoformat())
    db.add(sess)
    db.commit()
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("session_id", session_id, max_age=days * 86400, httponly=True)
    return response


@router.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    if session_id:
        sess = db.query(models.UserSession).filter(models.UserSession.id == session_id).first()
        if sess:
            db.delete(sess)
            db.commit()
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session_id")
    return response
