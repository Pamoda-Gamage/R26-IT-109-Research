import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.provider import Provider
from app.db.session import _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory() as session:
        yield session

router = APIRouter(prefix="/providers", tags=["providers"])

SERVICE_TYPES = ["plumbing", "carpentry", "electrical", "painting", "hvac", "roofing", "general"]
REGIONS = ["colombo-01", "colombo-02", "dehiwala", "mount-lavinia", "kotte"]
SERVICE_AREAS = ["colombo-01", "colombo-02", "dehiwala", "mount-lavinia", "kotte", "moratuwa", "ruwanella", "negombo"]


class ProviderCreateRequest(BaseModel):
    name: str
    service_type: str
    region: str
    lat: float
    lon: float
    rating: float | None = 4.5
    base_response_speed: float | None = 30.0
    profile_text: str | None = None
    phone: str | None = None
    years_experience: int | None = 1
    avatar_url: str | None = None
    service_areas: str | None = None


class ProviderUpdateRequest(BaseModel):
    name: str | None = None
    service_type: str | None = None
    region: str | None = None
    lat: float | None = None
    lon: float | None = None
    rating: float | None = None
    phone: str | None = None
    years_experience: int | None = None
    avatar_url: str | None = None
    service_areas: str | None = None


class ProviderResponse(BaseModel):
    id: str
    name: str
    service_type: str
    region: str
    lat: float
    lon: float
    rating: float
    years_experience: int
    phone: str | None
    avatar_url: str | None
    service_areas: str | None


@router.post("/", response_model=ProviderResponse)
async def create_provider(payload: ProviderCreateRequest, session: AsyncSession = Depends(get_db_session)):
    if payload.service_type not in SERVICE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid service_type. Must be one of {SERVICE_TYPES}")
    if payload.region not in REGIONS:
        raise HTTPException(status_code=400, detail=f"Invalid region. Must be one of {REGIONS}")

    provider = Provider(
        id=uuid.uuid4(),
        name=payload.name,
        service_type=payload.service_type,
        region=payload.region,
        lat=payload.lat,
        lon=payload.lon,
        rating=payload.rating or 4.5,
        years_experience=payload.years_experience or 1,
        phone=payload.phone,
        avatar_url=payload.avatar_url,
        service_areas=payload.service_areas,
        base_response_speed=payload.base_response_speed or 30.0,
        profile_text=payload.profile_text or "",
    )
    session.add(provider)
    await session.commit()
    await session.refresh(provider)

    try:
        import chromadb

        profile_text = (
            f"{provider.name}. {provider.service_type} provider with {provider.years_experience} years "
            f"experience in {provider.region}. Rating: {provider.rating}. {provider.profile_text}"
        )
        client = chromadb.PersistentClient(path="data/chroma")
        collection = client.get_or_create_collection("providers", metadata={"hnsw:space": "cosine"})
        collection.upsert(
            ids=[str(provider.id)],
            documents=[profile_text],
            metadatas=[{"service_type": provider.service_type, "region": provider.region}],
        )
    except Exception as err:
        print(f"Warning: Failed to embed new provider: {err}")

    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        service_type=provider.service_type,
        region=provider.region,
        lat=provider.lat,
        lon=provider.lon,
        rating=provider.rating,
        years_experience=provider.years_experience,
        phone=provider.phone,
        avatar_url=provider.avatar_url,
        service_areas=provider.service_areas,
    )


@router.get("/", response_model=list[ProviderResponse])
async def list_all_providers(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Provider))
    providers = result.scalars().all()
    return [
        ProviderResponse(
            id=str(p.id),
            name=p.name,
            service_type=p.service_type,
            region=p.region,
            lat=p.lat,
            lon=p.lon,
            rating=p.rating,
            years_experience=p.years_experience,
            phone=p.phone,
            avatar_url=p.avatar_url,
            service_areas=p.service_areas,
        )
        for p in providers
    ]


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str, session: AsyncSession = Depends(get_db_session)):
    try:
        provider_uuid = uuid.UUID(provider_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid provider ID format") from err

    result = await session.execute(select(Provider).where(Provider.id == provider_uuid))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        service_type=provider.service_type,
        region=provider.region,
        lat=provider.lat,
        lon=provider.lon,
        rating=provider.rating,
        years_experience=provider.years_experience,
        phone=provider.phone,
        avatar_url=provider.avatar_url,
        service_areas=provider.service_areas,
    )


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    payload: ProviderUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        provider_uuid = uuid.UUID(provider_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid provider ID format") from err

    result = await session.execute(select(Provider).where(Provider.id == provider_uuid))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if payload.service_type and payload.service_type not in SERVICE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid service_type. Must be one of {SERVICE_TYPES}")
    if payload.region and payload.region not in REGIONS:
        raise HTTPException(status_code=400, detail=f"Invalid region. Must be one of {REGIONS}")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(provider, key, value)

    await session.commit()
    await session.refresh(provider)

    return ProviderResponse(
        id=str(provider.id),
        name=provider.name,
        service_type=provider.service_type,
        region=provider.region,
        lat=provider.lat,
        lon=provider.lon,
        rating=provider.rating,
        years_experience=provider.years_experience,
        phone=provider.phone,
        avatar_url=provider.avatar_url,
        service_areas=provider.service_areas,
    )


@router.delete("/{provider_id}")
async def delete_provider(provider_id: str, session: AsyncSession = Depends(get_db_session)):
    try:
        provider_uuid = uuid.UUID(provider_id)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid provider ID format") from err

    result = await session.execute(select(Provider).where(Provider.id == provider_uuid))
    provider = result.scalar_one_or_none()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await session.delete(provider)
    await session.commit()
    return {"message": "Provider deleted"}


class ImageUploadRequest(BaseModel):
    data: str
    filename: str | None = None


@router.post("/upload/image")
async def upload_image(payload: ImageUploadRequest, request: Request):
    import base64
    import imghdr
    from pathlib import Path

    if not payload.data.startswith("data:image/"):
        msg = "Invalid image data format"
        raise HTTPException(status_code=400, detail=msg)

    try:
        header, encoded = payload.data.split(",", 1)
        image_data = base64.b64decode(encoded)
    except (ValueError, TypeError) as err:
        msg = "Failed to decode image data"
        raise HTTPException(status_code=400, detail=msg) from err

    image_type = imghdr.what(None, h=image_data)
    if image_type not in ("jpeg", "png", "webp"):
        msg = "Only JPEG, PNG, and WebP images allowed"
        raise HTTPException(status_code=400, detail=msg)

    if len(image_data) > 5 * 1024 * 1024:
        msg = "File size must be under 5MB"
        raise HTTPException(status_code=400, detail=msg)

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    ext = "jpg" if image_type == "jpeg" else image_type
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = upload_dir / filename

    with open(filepath, "wb") as f:
        f.write(image_data)

    base_url = f"{request.url.scheme}://{request.url.netloc}"
    return {"url": f"{base_url}/uploads/{filename}", "filename": filename}


@router.get("/service-types")
async def get_service_types():
    return {"service_types": SERVICE_TYPES}


@router.get("/regions")
async def get_regions():
    return {"regions": REGIONS}


@router.get("/service-areas")
async def get_service_areas():
    return {"service_areas": SERVICE_AREAS}


@router.get("/list")
async def list_providers(
    service_type: str | None = None,
    region: str | None = None,
    session: AsyncSession = Depends(get_db_session),
):
    query = select(Provider)
    if service_type:
        query = query.where(Provider.service_type == service_type)
    if region:
        query = query.where(Provider.region == region)

    result = await session.execute(query)
    providers = result.scalars().all()

    return {
        "providers": [
            ProviderResponse(
                id=str(p.id),
                name=p.name,
                service_type=p.service_type,
                region=p.region,
                lat=p.lat,
                lon=p.lon,
                rating=p.rating,
                years_experience=p.years_experience,
                phone=p.phone,
                avatar_url=p.avatar_url,
                service_areas=p.service_areas,
            )
            for p in providers
        ],
        "filters": {"service_type": service_type, "region": region},
    }
