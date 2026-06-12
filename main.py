import os
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from config import APP_NAME, APP_VERSION
from database import SessionLocal, UserSession, User, init_db
from routers import auth, pages, bottles, tastings, wishlist, barcode, admin, settings

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.mount("/static", StaticFiles(directory="static"), name="static")

os.makedirs("static/uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

init_db()

_PUBLIC_PATHS = {"/login", "/setup"}
_PUBLIC_PREFIXES = ("/static/",)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            return await call_next(request)

        session_id = request.cookies.get("session_id")
        user = None
        if session_id:
            db = SessionLocal()
            try:
                sess = db.query(UserSession).filter(UserSession.id == session_id).first()
                if sess:
                    exp = datetime.fromisoformat(sess.expires_at)
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) < exp:
                        user = db.query(User).filter(User.id == sess.user_id, User.is_active == True).first()
                    else:
                        db.delete(sess)
                        db.commit()
            finally:
                db.close()

        if not user:
            response = RedirectResponse(url="/login", status_code=302)
            response.delete_cookie("session_id")
            return response

        request.state.user = user
        return await call_next(request)


app.add_middleware(AuthMiddleware)

app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(bottles.router)
app.include_router(tastings.router)
app.include_router(wishlist.router)
app.include_router(barcode.router)
app.include_router(admin.router)
app.include_router(settings.router)
