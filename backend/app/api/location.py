from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.location_service import search_nearby
from typing import Optional

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/nearby")
async def nearby(
        lat: float = Query(..., description="Широта"),
        lng: float = Query(..., description="Долгота"),
        radius_km: float = Query(5.0, description="Радиус в км"),
        limit: int = Query(10, description="Лимит результатов"),
        types: Optional[str] = Query("organization,volunteer,foster_request", description="Типы через запятую"),
        db: AsyncSession = Depends(get_db)
):
    types_list = [t.strip() for t in types.split(",")] if types else []

    from app.schemas.location import LocationNearbyRequest
    req = LocationNearbyRequest(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        limit=limit,
        types=types_list
    )

    try:
        items = await search_nearby(db, req)
        return {"items": items}
    except Exception as e:
        raise HTTPException(500, detail=f"Search failed: {e}")