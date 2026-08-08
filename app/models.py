from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid4())


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120))
    address_line: Mapped[str] = mapped_column(String(200))
    suburb: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(12), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    listings: Mapped[list[Listing]] = relationship(back_populates="location")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    listings: Mapped[list[Listing]] = relationship(back_populates="category")


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), index=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending")
    analysis_provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_text: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    analysis_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    location: Mapped[Location] = relationship(back_populates="listings")
    category: Mapped[Category | None] = relationship(back_populates="listings")
    images: Mapped[list[Image]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="Image.sort_order",
    )


class Image(Base):
    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    listing_id: Mapped[str] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    storage_name: Mapped[str] = mapped_column(String(160), unique=True)
    original_name: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(30))
    byte_size: Mapped[int] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    listing: Mapped[Listing] = relationship(back_populates="images")


CATEGORY_SEED: list[dict[str, Any]] = [
    {"slug": "clothing", "name": "Clothing"},
    {"slug": "footwear", "name": "Footwear"},
    {"slug": "accessories", "name": "Accessories"},
    {"slug": "homeware", "name": "Homeware"},
    {"slug": "furniture", "name": "Furniture"},
    {"slug": "electronics", "name": "Electronics"},
    {"slug": "books-media", "name": "Books & Media"},
    {"slug": "sports-outdoors", "name": "Sports & Outdoors"},
    {"slug": "toys-games", "name": "Toys & Games"},
    {"slug": "collectibles", "name": "Collectibles"},
    {"slug": "other", "name": "Other"},
]

