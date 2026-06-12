from __future__ import annotations

import os
import uuid
from typing import Generator

import bcrypt
from fastapi import UploadFile
from sqlalchemy.orm import Session

from config import UPLOAD_DIR
from database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_pw(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def save_uploaded_file(file: UploadFile | None, prefix: str = "img") -> str | None:
    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
    dest = os.path.join(UPLOAD_DIR, filename)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    return f"static/uploads/{filename}"
