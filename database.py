from sqlalchemy import (
    Boolean, Column, Float, ForeignKey, Integer, String, Text, create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

DATABASE_URL = "sqlite:///./data/cellar.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


class Bottle(Base):
    __tablename__ = "bottles"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    name = Column(String)
    whiskey_type = Column(String)
    region = Column(String)
    country = Column(String)
    age_statement = Column(Integer)        # years; None = NAS
    vintage_year = Column(Integer)
    abv = Column(Float)
    volume_ml = Column(Integer, default=750)
    price_paid = Column(Float)
    date_acquired = Column(String)
    upc = Column(String)
    status = Column(String, default="sealed")  # sealed / opened / finished
    image_path_1 = Column(String)
    image_path_2 = Column(String)
    notes = Column(Text)
    liked = Column(Boolean)
    buy_again = Column(Boolean)
    rating = Column(Float)
    is_deleted = Column(Boolean, default=False)
    is_sold = Column(Boolean, default=False)
    price_sold = Column(Float)
    is_gift = Column(Boolean, default=False)
    is_collectible = Column(Boolean, default=False)

    tastings = relationship("Tasting", back_populates="bottle", cascade="all, delete-orphan")


class Tasting(Base):
    __tablename__ = "tastings"

    id = Column(Integer, primary_key=True, index=True)
    bottle_id = Column(Integer, ForeignKey("bottles.id"), nullable=False)
    date_tasted = Column(String)
    rating = Column(Float)
    liked = Column(Boolean)
    buy_again = Column(Boolean)
    nose = Column(Text)
    palate = Column(Text)
    finish = Column(Text)
    overall = Column(Text)

    bottle = relationship("Bottle", back_populates="tastings")


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String)
    name = Column(String)
    whiskey_type = Column(String)
    region = Column(String)
    priority = Column(String, default="Medium")
    est_price = Column(Float)
    url = Column(String)
    notes = Column(Text)
    image_path = Column(String)
    created_at = Column(String)


class UpcCache(Base):
    __tablename__ = "upc_cache"

    upc = Column(String, primary_key=True)
    title = Column(String)
    brand = Column(String)
    name = Column(String)
    whiskey_type = Column(String)
    region = Column(String)
    country = Column(String)
    age_statement = Column(Integer)
    abv = Column(Float)
    volume_ml = Column(Integer)
    image_path = Column(String)
    updated_at = Column(String)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(String)

    user = relationship("User", back_populates="sessions")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String)
    value = Column(String)

    user = relationship("User", back_populates="preferences")


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String)


def _col_exists(db: Session, table: str, column: str) -> bool:
    result = db.execute(__import__("sqlalchemy").text(f"PRAGMA table_info({table})"))
    return any(row[1] == column for row in result)


def init_db():
    Base.metadata.create_all(bind=engine)

    # Forward-compatible migrations: add columns to existing databases
    with Session(engine) as db:
        migrations = [
            ("bottles", "liked", "ALTER TABLE bottles ADD COLUMN liked BOOLEAN"),
            ("bottles", "buy_again", "ALTER TABLE bottles ADD COLUMN buy_again BOOLEAN"),
            ("bottles", "rating", "ALTER TABLE bottles ADD COLUMN rating REAL"),
            ("bottles", "vintage_year", "ALTER TABLE bottles ADD COLUMN vintage_year INTEGER"),
            ("bottles", "is_sold", "ALTER TABLE bottles ADD COLUMN is_sold BOOLEAN DEFAULT 0"),
            ("bottles", "price_sold", "ALTER TABLE bottles ADD COLUMN price_sold REAL"),
            ("bottles", "image_path_2", "ALTER TABLE bottles ADD COLUMN image_path_2 TEXT"),
            ("bottles", "country", "ALTER TABLE bottles ADD COLUMN country TEXT"),
            ("bottles", "is_gift", "ALTER TABLE bottles ADD COLUMN is_gift BOOLEAN DEFAULT 0"),
            ("bottles", "is_collectible", "ALTER TABLE bottles ADD COLUMN is_collectible BOOLEAN DEFAULT 0"),
        ]
        for table, col, sql in migrations:
            if not _col_exists(db, table, col):
                db.execute(__import__("sqlalchemy").text(sql))
        db.commit()
