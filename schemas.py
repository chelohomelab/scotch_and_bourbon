from typing import Optional
from pydantic import BaseModel


class BottlePatchPayload(BaseModel):
    brand: Optional[str] = None
    name: Optional[str] = None
    whiskey_type: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    age_statement: Optional[int] = None
    vintage_year: Optional[int] = None
    abv: Optional[float] = None
    volume_ml: Optional[int] = None
    price_paid: Optional[float] = None
    date_acquired: Optional[str] = None
    upc: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    liked: Optional[bool] = None
    buy_again: Optional[bool] = None
    rating: Optional[float] = None


class SoldPayload(BaseModel):
    price_sold: Optional[float] = None


class TastingPayload(BaseModel):
    date_tasted: Optional[str] = None
    rating: Optional[float] = None
    liked: Optional[bool] = None
    buy_again: Optional[bool] = None
    nose: Optional[str] = None
    palate: Optional[str] = None
    finish: Optional[str] = None
    overall: Optional[str] = None


class WishlistPatchPayload(BaseModel):
    brand: Optional[str] = None
    name: Optional[str] = None
    whiskey_type: Optional[str] = None
    region: Optional[str] = None
    priority: Optional[str] = None
    est_price: Optional[float] = None
    url: Optional[str] = None
    notes: Optional[str] = None


class AdminUserPatch(BaseModel):
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class SettingsPatch(BaseModel):
    value: str
