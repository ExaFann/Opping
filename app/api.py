from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Category, Image, Listing, Location
from app.schemas import (
    AnalysisResponse,
    CategoryResponse,
    HealthResponse,
    ImageResponse,
    ListingPage,
    ListingResponse,
    ListingUpdate,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.services.ai import ImageInput
from app.services.storage import PreparedImage, StorageValidationError


router = APIRouter()


def listing_query():
    return (
        select(Listing)
        .options(
            selectinload(Listing.location),
            selectinload(Listing.category),
            selectinload(Listing.images),
        )
        .execution_options(populate_existing=True)
    )


def load_listing(db: Session, listing_id: str) -> Listing:
    listing = db.scalar(listing_query().where(Listing.id == listing_id))
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


def serialize_listing(listing: Listing) -> ListingResponse:
    return ListingResponse(
        id=listing.id,
        status=listing.status,
        location=LocationResponse.model_validate(listing.location),
        category=(
            CategoryResponse.model_validate(listing.category) if listing.category else None
        ),
        images=[
            ImageResponse(
                id=image.id,
                original_name=image.original_name,
                mime_type=image.mime_type,
                byte_size=image.byte_size,
                sort_order=image.sort_order,
                url=f"/media/{image.storage_name}",
            )
            for image in listing.images
        ],
        analysis=AnalysisResponse(
            status=listing.analysis_status,
            provider=listing.analysis_provider,
            summary=listing.ai_summary,
            detected_text=listing.detected_text or [],
            confidence=listing.ai_confidence,
            error=listing.analysis_error,
        ),
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        published_at=listing.published_at,
    )


async def prepare_uploads(request: Request, uploads: list[UploadFile]) -> list[PreparedImage]:
    settings = request.app.state.settings
    if not uploads:
        raise HTTPException(status_code=422, detail="At least one image is required")
    if len(uploads) > settings.max_images_per_listing:
        raise HTTPException(
            status_code=422,
            detail=f"A listing can have at most {settings.max_images_per_listing} images",
        )
    try:
        return [await request.app.state.storage.prepare(upload) for upload in uploads]
    except StorageValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


async def analyze_listing(request: Request, db: Session, listing: Listing) -> bool:
    provider = request.app.state.ai_provider
    listing.analysis_status = "running"
    listing.analysis_provider = provider.name
    listing.analysis_error = None
    db.commit()

    try:
        images = [
            ImageInput(
                data=request.app.state.storage.read(image.storage_name),
                mime_type=image.mime_type,
            )
            for image in listing.images
        ]
        categories = list(db.scalars(select(Category).order_by(Category.id)))
        result = await run_in_threadpool(
            provider.analyze, images, [category.slug for category in categories]
        )
        category_by_slug = {category.slug: category for category in categories}
        listing.category_id = category_by_slug[result.category_slug].id
        listing.analysis_status = "succeeded"
        listing.ai_summary = result.summary
        listing.detected_text = result.detected_text
        listing.ai_confidence = result.confidence
        listing.analysis_error = None
        db.commit()
        return True
    except Exception as exc:
        db.rollback()
        failed_listing = db.get(Listing, listing.id)
        if failed_listing is None:
            raise
        failed_listing.analysis_status = "failed"
        failed_listing.analysis_provider = provider.name
        failed_listing.analysis_error = str(exc)[:1000]
        db.commit()
        return False


@router.get("/health", response_model=HealthResponse)
def health(request: Request, db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(select(1))
    return HealthResponse(
        status="ok",
        database="ok",
        ai_provider=request.app.state.ai_provider.name,
    )


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.id)))


@router.get("/locations", response_model=list[LocationResponse])
def list_locations(db: Session = Depends(get_db)) -> list[Location]:
    return list(db.scalars(select(Location).order_by(Location.name, Location.created_at)))


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)) -> Location:
    location = Location(**payload.model_dump())
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.patch("/locations/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: UUID, payload: LocationUpdate, db: Session = Depends(get_db)
) -> Location:
    location = db.get(Location, str(location_id))
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    updates = payload.model_dump(exclude_unset=True)
    for required_field in ("name", "address_line", "city"):
        if required_field in updates and updates[required_field] is None:
            raise HTTPException(status_code=422, detail=f"{required_field} cannot be null")
    for field, value in updates.items():
        setattr(location, field, value)
    db.commit()
    db.refresh(location)
    return location


@router.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    request: Request,
    location_id: UUID = Form(...),
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> ListingResponse:
    location = db.get(Location, str(location_id))
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    prepared = await prepare_uploads(request, images)
    listing = Listing(location_id=str(location_id))
    db.add(listing)
    try:
        db.flush()
        for index, image in enumerate(prepared):
            storage_name = request.app.state.storage.save(listing.id, image)
            listing.images.append(
                Image(
                    storage_name=storage_name,
                    original_name=image.original_name,
                    mime_type=image.mime_type,
                    byte_size=len(image.data),
                    sort_order=index,
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        request.app.state.storage.delete_listing(listing.id)
        raise

    listing = load_listing(db, listing.id)
    await analyze_listing(request, db, listing)
    return serialize_listing(load_listing(db, listing.id))


@router.get("/listings/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: UUID, db: Session = Depends(get_db)) -> ListingResponse:
    return serialize_listing(load_listing(db, str(listing_id)))


@router.patch("/listings/{listing_id}", response_model=ListingResponse)
def update_listing(
    listing_id: UUID, payload: ListingUpdate, db: Session = Depends(get_db)
) -> ListingResponse:
    listing = load_listing(db, str(listing_id))
    updates = payload.model_dump(exclude_unset=True)
    if "location_id" in updates:
        if updates["location_id"] is None:
            raise HTTPException(status_code=422, detail="location_id cannot be null")
        location_id = str(updates["location_id"])
        if db.get(Location, location_id) is None:
            raise HTTPException(status_code=404, detail="Location not found")
        listing.location_id = location_id
    if "category_id" in updates:
        if updates["category_id"] is None:
            listing.category_id = None
        elif db.get(Category, updates["category_id"]) is None:
            raise HTTPException(status_code=404, detail="Category not found")
        else:
            listing.category_id = updates["category_id"]
    db.commit()
    return serialize_listing(load_listing(db, listing.id))


@router.post("/listings/{listing_id}/images", response_model=ListingResponse)
async def add_listing_images(
    listing_id: UUID,
    request: Request,
    images: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> ListingResponse:
    listing = load_listing(db, str(listing_id))
    maximum = request.app.state.settings.max_images_per_listing
    if len(listing.images) + len(images) > maximum:
        raise HTTPException(status_code=422, detail=f"A listing can have at most {maximum} images")
    prepared = await prepare_uploads(request, images)
    saved_names: list[str] = []
    try:
        next_order = len(listing.images)
        for index, image in enumerate(prepared):
            storage_name = request.app.state.storage.save(listing.id, image)
            saved_names.append(storage_name)
            listing.images.append(
                Image(
                    storage_name=storage_name,
                    original_name=image.original_name,
                    mime_type=image.mime_type,
                    byte_size=len(image.data),
                    sort_order=next_order + index,
                )
            )
        listing.analysis_status = "pending"
        listing.analysis_provider = None
        listing.ai_summary = None
        listing.detected_text = []
        listing.ai_confidence = None
        listing.analysis_error = None
        db.commit()
    except Exception:
        db.rollback()
        for storage_name in saved_names:
            request.app.state.storage.delete(storage_name)
        raise
    return serialize_listing(load_listing(db, listing.id))


@router.delete("/listings/{listing_id}/images/{image_id}", response_model=ListingResponse)
def delete_listing_image(
    listing_id: UUID,
    image_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> ListingResponse:
    listing = load_listing(db, str(listing_id))
    if len(listing.images) == 1:
        raise HTTPException(status_code=409, detail="A listing must retain at least one image")
    image = next((item for item in listing.images if item.id == str(image_id)), None)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found on this listing")
    storage_name = image.storage_name
    db.delete(image)
    remaining = [item for item in listing.images if item.id != image.id]
    for index, remaining_image in enumerate(remaining):
        remaining_image.sort_order = index
    listing.analysis_status = "pending"
    listing.analysis_provider = None
    listing.ai_summary = None
    listing.detected_text = []
    listing.ai_confidence = None
    listing.analysis_error = None
    db.commit()
    request.app.state.storage.delete(storage_name)
    return serialize_listing(load_listing(db, listing.id))


@router.post("/listings/{listing_id}/analyze", response_model=ListingResponse)
async def retry_analysis(
    listing_id: UUID, request: Request, db: Session = Depends(get_db)
) -> ListingResponse:
    listing = load_listing(db, str(listing_id))
    succeeded = await analyze_listing(request, db, listing)
    if not succeeded:
        raise HTTPException(status_code=502, detail="AI analysis failed; the draft was preserved")
    return serialize_listing(load_listing(db, listing.id))


@router.post("/listings/{listing_id}/publish", response_model=ListingResponse)
def publish_listing(listing_id: UUID, db: Session = Depends(get_db)) -> ListingResponse:
    listing = load_listing(db, str(listing_id))
    if listing.status == "published":
        raise HTTPException(status_code=409, detail="Listing is already published")
    if listing.category_id is None:
        raise HTTPException(status_code=422, detail="Choose a category before publishing")
    if not listing.images:
        raise HTTPException(status_code=422, detail="A listing needs at least one image")
    listing.status = "published"
    listing.published_at = datetime.now(timezone.utc)
    db.commit()
    return serialize_listing(load_listing(db, listing.id))


@router.get("/listings", response_model=ListingPage)
def list_published_listings(
    category: str | None = Query(default=None, description="Category slug"),
    location_id: UUID | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ListingPage:
    filters = [Listing.status == "published"]
    if category:
        filters.append(Category.slug == category)
    if location_id:
        filters.append(Listing.location_id == str(location_id))

    count_statement = select(func.count(Listing.id)).outerjoin(Category).where(*filters)
    total = db.scalar(count_statement) or 0
    statement = (
        listing_query()
        .outerjoin(Category)
        .where(*filters)
        .order_by(Listing.published_at.desc(), Listing.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(statement).unique())
    return ListingPage(
        items=[serialize_listing(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )
