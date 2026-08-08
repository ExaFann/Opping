from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address_line: str = Field(min_length=1, max_length=200)
    suburb: str | None = Field(default=None, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=12)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address_line: str | None = Field(default=None, min_length=1, max_length=200)
    suburb: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    postcode: str | None = Field(default=None, max_length=12)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str


class ListingUpdate(BaseModel):
    location_id: UUID | None = None
    category_id: int | None = None


class ImageResponse(BaseModel):
    id: UUID
    original_name: str
    mime_type: str
    byte_size: int
    sort_order: int
    url: str


class AnalysisResponse(BaseModel):
    status: str
    provider: str | None
    summary: str | None
    detected_text: list[str]
    confidence: float | None
    error: str | None = None


class ListingResponse(BaseModel):
    id: UUID
    status: str
    location: LocationResponse
    category: CategoryResponse | None
    images: list[ImageResponse]
    analysis: AnalysisResponse
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class ListingPage(BaseModel):
    items: list[ListingResponse]
    page: int
    page_size: int
    total: int


class HealthResponse(BaseModel):
    status: str
    database: str
    ai_provider: str


class AIOutput(BaseModel):
    category_slug: str
    confidence: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=500)
    detected_text: list[str] = Field(default_factory=list)

