from sqlalchemy import select, func, text, null
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import Organization
from app.models.volunteer import VolunteerProfile
from app.models.foster import FosterRequest
from app.schemas.location import LocationNearbyRequest
from typing import List, Dict, Any
from app.models.user import User

DEG_PER_KM = 1 / 111.0

async def search_nearby(
    db: AsyncSession,
    req: LocationNearbyRequest
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    delta_deg = req.radius_km * DEG_PER_KM
    lat_min, lat_max = req.lat - delta_deg, req.lat + delta_deg
    lng_min, lng_max = req.lng - delta_deg, req.lng + delta_deg

    if "organization" in req.types:
        stmt = (
            select(
                Organization.id,
                Organization.name,
                Organization.address,
                Organization.address_lat,
                Organization.address_lng,
                func.sqrt(
                    func.pow(func.radians(Organization.address_lat) - func.radians(req.lat), 2) +
                    func.pow(func.radians(Organization.address_lng) - func.radians(req.lng), 2)
                ).label("dist_rad")
            )
            .where(
                Organization.address_lat.is_not(None),
                Organization.address_lng.is_not(None),
                Organization.address_lat.between(lat_min, lat_max),
                Organization.address_lng.between(lng_min, lng_max)
            )
            .order_by("dist_rad")
            .limit(req.limit)
        )
        res = await db.execute(stmt)
        for r in res.all():
            results.append({
                "type": "organization",
                "id": r.id,
                "name": r.name,
                "address": r.address,
                "lat": float(r.address_lat),
                "lng": float(r.address_lng),
                "distance_m": float(r.dist_rad * 6371000)
            })

    if "volunteer" in req.types:
        stmt = (
            select(
                VolunteerProfile.user_id.label("id"),
                User.name.label("name"),
                null().label("address"),
                VolunteerProfile.location_lat,
                VolunteerProfile.location_lng,
                func.sqrt(
                    func.pow(func.radians(VolunteerProfile.location_lat) - func.radians(req.lat), 2) +
                    func.pow(func.radians(VolunteerProfile.location_lng) - func.radians(req.lng), 2)
                ).label("dist_rad")
            )
            .join(User, VolunteerProfile.user_id == User.id)
            .where(
                VolunteerProfile.location_lat.is_not(None),
                VolunteerProfile.location_lng.is_not(None),
                VolunteerProfile.location_lat.between(lat_min, lat_max),
                VolunteerProfile.location_lng.between(lng_min, lng_max)
            )
            .order_by("dist_rad")
            .limit(req.limit)
        )
        res = await db.execute(stmt)
        for r in res.all():
            results.append({
                "type": "volunteer",
                "id": r.id,
                "name": r.name,
                "address": None,
                "lat": float(r.location_lat),
                "lng": float(r.location_lng),
                "distance_m": float(r.dist_rad * 6371000)
            })

    if "foster_request" in req.types:
        stmt = (
            select(
                FosterRequest.id,
                User.name.label("name"),
                null().label("address"),
                FosterRequest.pickup_lat,
                FosterRequest.pickup_lng,
                func.sqrt(
                    func.pow(func.radians(FosterRequest.pickup_lat) - func.radians(req.lat), 2) +
                    func.pow(func.radians(FosterRequest.pickup_lng) - func.radians(req.lng), 2)
                ).label("dist_rad")
            )
            .join(User, FosterRequest.owner_id == User.id)
            .where(
                FosterRequest.pickup_lat.is_not(None),
                FosterRequest.pickup_lng.is_not(None),
                FosterRequest.pickup_lat.between(lat_min, lat_max),
                FosterRequest.pickup_lng.between(lng_min, lng_max)
            )
            .order_by("dist_rad")
            .limit(req.limit)
        )
        res = await db.execute(stmt)
        for r in res.all():
            results.append({
                "type": "foster_request",
                "id": r.id,
                "name": f"Запрос от {r.name}",
                "address": None,
                "lat": float(r.pickup_lat),
                "lng": float(r.pickup_lng),
                "distance_m": float(r.dist_rad * 6371000)
            })

    results.sort(key=lambda x: x["distance_m"])
    return results[:req.limit]