from __future__ import annotations

import html
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import database as models
from dependencies import get_db

router = APIRouter(prefix="/barcode", tags=["barcode"])

WHISKEY_TYPE_KEYWORDS = [
    ("single malt scotch", "Single Malt Scotch"),
    ("blended malt scotch", "Blended Malt Scotch"),
    ("single grain scotch", "Single Grain Scotch"),
    ("blended scotch", "Blended Scotch"),
    ("scotch whisky", "Blended Scotch"),
    ("scotch", "Blended Scotch"),
    ("bourbon whiskey", "Bourbon"),
    ("bourbon", "Bourbon"),
    ("tennessee whiskey", "Tennessee Whiskey"),
    ("rye whiskey", "Rye Whiskey"),
    ("irish whiskey", "Irish Whiskey"),
    ("japanese whisky", "Japanese Whisky"),
    ("canadian whisky", "Canadian Whisky"),
    ("single malt", "Single Malt Scotch"),
    ("blended malt", "Blended Malt Scotch"),
]

REGION_KEYWORDS = {
    "speyside": "Speyside",
    "highland": "Highlands",
    "highlands": "Highlands",
    "islay": "Islay",
    "lowland": "Lowlands",
    "lowlands": "Lowlands",
    "campbeltown": "Campbeltown",
    "islands": "Islands",
    "island": "Islands",
    "kentucky": "Kentucky",
    "tennessee": "Tennessee",
}


def _parse_whiskey_type(title: str) -> str | None:
    t = title.lower()
    for keyword, wtype in WHISKEY_TYPE_KEYWORDS:
        if keyword in t:
            return wtype
    if "whiskey" in t or "whisky" in t:
        return "World Whisky"
    return None


def _parse_age(title: str) -> int | None:
    m = re.search(r"(\d+)\s*[-–]?\s*(?:year|yr)s?", title, re.IGNORECASE)
    if m:
        val = int(m.group(1))
        if 1 <= val <= 60:
            return val
    return None


def _parse_abv(title: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", title)
    if m:
        val = float(m.group(1))
        if 20.0 <= val <= 70.0:
            return val
    return None


def _parse_volume(title: str) -> int | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*ml", title, re.IGNORECASE)
    if m:
        return int(float(m.group(1)))
    m = re.search(r"(\d+(?:\.\d+)?)\s*l(?:iter|itre)?(?:\b|$)", title, re.IGNORECASE)
    if m:
        return int(float(m.group(1)) * 1000)
    return None


def _parse_region(title: str) -> str | None:
    t = title.lower()
    for key, val in REGION_KEYWORDS.items():
        if key in t:
            return val
    return None


def _parse_country(title: str, whiskey_type: str | None) -> str | None:
    t = title.lower()
    if whiskey_type in ("Single Malt Scotch", "Blended Scotch", "Blended Malt Scotch", "Single Grain Scotch"):
        return "Scotland"
    if whiskey_type in ("Bourbon", "Tennessee Whiskey", "Rye Whiskey"):
        return "United States"
    if whiskey_type == "Irish Whiskey":
        return "Ireland"
    if whiskey_type == "Japanese Whisky":
        return "Japan"
    if whiskey_type == "Canadian Whisky":
        return "Canada"
    if "scotland" in t or "scottish" in t:
        return "Scotland"
    if "ireland" in t or "irish" in t:
        return "Ireland"
    if "japan" in t or "japanese" in t:
        return "Japan"
    return None


def _parse_brand(api_brand: str, title: str) -> str | None:
    if api_brand and len(api_brand) > 1:
        return api_brand
    known_brands = [
        "Glenfiddich", "Macallan", "Glenlivet", "Laphroaig", "Ardbeg", "Lagavulin",
        "Oban", "Dalmore", "Highland Park", "Glenmorangie", "Balvenie", "Bowmore",
        "Bruichladdich", "Caol Ila", "Springbank", "Glenfarclas", "Aberfeldy",
        "Jack Daniel", "Jim Beam", "Maker's Mark", "Wild Turkey", "Bulleit",
        "Woodford Reserve", "Buffalo Trace", "Four Roses", "Knob Creek",
        "Jameson", "Bushmills", "Redbreast", "Green Spot", "Yellow Spot",
        "Suntory", "Nikka", "Yamazaki", "Hakushu", "Hibiki",
        "Crown Royal", "Canadian Club", "Seagram",
        "Johnnie Walker", "Chivas Regal", "Dewar's", "Monkey Shoulder",
    ]
    t = title.lower()
    for brand in known_brands:
        if brand.lower() in t:
            return brand
    return None


def _download_upc_image(upc: str, img_url: str) -> str | None:
    try:
        dest_dir = "static/uploads/upc_cache"
        os.makedirs(dest_dir, exist_ok=True)
        ext = os.path.splitext(urllib.parse.urlsplit(img_url).path)[1].lower() or ".jpg"
        filename = f"upc_{upc}{ext}"
        dest = os.path.join(dest_dir, filename)
        if os.path.exists(dest):
            return f"static/uploads/upc_cache/{filename}"
        req = urllib.request.Request(img_url, headers={"User-Agent": "homelab-cellar/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            with open(dest, "wb") as f:
                f.write(resp.read())
        return f"static/uploads/upc_cache/{filename}"
    except Exception:
        return None


def upsert_upc_cache(
    db: Session,
    upc: str,
    title: str | None = None,
    brand: str | None = None,
    name: str | None = None,
    whiskey_type: str | None = None,
    region: str | None = None,
    country: str | None = None,
    age_statement: int | None = None,
    abv: float | None = None,
    volume_ml: int | None = None,
    image_path: str | None = None,
) -> models.UpcCache:
    cached = db.query(models.UpcCache).filter(models.UpcCache.upc == upc).first()
    now = datetime.now(timezone.utc).isoformat()
    if cached:
        if title:        cached.title = title
        if brand:        cached.brand = brand
        if name:         cached.name = name
        if whiskey_type: cached.whiskey_type = whiskey_type
        if region:       cached.region = region
        if country:      cached.country = country
        if age_statement is not None: cached.age_statement = age_statement
        if abv is not None:           cached.abv = abv
        if volume_ml is not None:     cached.volume_ml = volume_ml
        if image_path:   cached.image_path = image_path
        cached.updated_at = now
    else:
        cached = models.UpcCache(
            upc=upc, title=title, brand=brand, name=name,
            whiskey_type=whiskey_type, region=region, country=country,
            age_statement=age_statement, abv=abv, volume_ml=volume_ml,
            image_path=image_path, updated_at=now,
        )
        db.add(cached)
    db.commit()
    return cached


def _cache_to_response(c: models.UpcCache) -> dict:
    return {
        "upc": c.upc, "title": c.title, "brand": c.brand, "name": c.name,
        "whiskey_type": c.whiskey_type, "region": c.region, "country": c.country,
        "age_statement": c.age_statement, "abv": c.abv, "volume_ml": c.volume_ml,
        "image_path": c.image_path, "source": "cache",
    }


def _lookup_upcitemdb(upc: str) -> dict | None:
    url = f"https://api.upcitemdb.com/prod/trial/lookup?upc={urllib.parse.quote(upc)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "homelab-cellar/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        items = data.get("items", [])
        return items[0] if items else None
    except Exception:
        return None


def _lookup_openfoodfacts(upc: str) -> dict | None:
    url = f"https://world.openfoodfacts.org/api/v2/product/{urllib.parse.quote(upc)}.json?fields=product_name,brands,quantity,image_url"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "homelab-cellar/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") == 1:
            return data.get("product")
    except Exception:
        pass
    return None


@router.get("/lookup")
def lookup_barcode(upc: str, db: Session = Depends(get_db)):
    upc = upc.strip()
    if not upc:
        raise HTTPException(400, "UPC required")

    # 1. Local cache
    cached = db.query(models.UpcCache).filter(models.UpcCache.upc == upc).first()
    if cached:
        return _cache_to_response(cached)

    # 2. UPC Item DB
    item = _lookup_upcitemdb(upc)
    if item:
        title = item.get("title") or item.get("description") or ""
        raw_brand = html.unescape(item.get("brand") or "")
        api_images = item.get("images") or []
    else:
        # 3. Open Food Facts fallback
        off = _lookup_openfoodfacts(upc)
        if off:
            title = off.get("product_name") or ""
            raw_brand = off.get("brands") or ""
            api_images = [off.get("image_url")] if off.get("image_url") else []
        else:
            raise HTTPException(404, "Product not found in any database")

    whiskey_type = _parse_whiskey_type(title)
    brand = _parse_brand(raw_brand, title)
    age = _parse_age(title)
    abv = _parse_abv(title)
    volume_ml = _parse_volume(title)
    region = _parse_region(title)
    country = _parse_country(title, whiskey_type)

    # Attempt to extract product name (expression) from title
    name = None
    if brand and title:
        name_raw = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE).strip(" -,")
        name = name_raw if name_raw else None

    image_path = None
    for img_url in api_images:
        if img_url:
            image_path = _download_upc_image(upc, img_url)
            if image_path:
                break

    upsert_upc_cache(
        db, upc, title=title, brand=brand, name=name,
        whiskey_type=whiskey_type, region=region, country=country,
        age_statement=age, abv=abv, volume_ml=volume_ml, image_path=image_path,
    )

    return {
        "upc": upc, "title": title, "brand": brand, "name": name,
        "whiskey_type": whiskey_type, "region": region, "country": country,
        "age_statement": age, "abv": abv, "volume_ml": volume_ml,
        "image_path": image_path, "source": "api",
    }
