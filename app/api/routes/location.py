from typing import Optional, List
from geopy.geocoders import Nominatim
from fastapi import APIRouter, Request, Query
from app.api.deps import SessionDep, get_db
from app.crud import get_address
from app.models.message import LocationResponse

router = APIRouter()

@router.get("/", response_model=LocationResponse)
def get_location(
    lat: float = Query(...),
    lon: float = Query(...),
):
    address = get_address(lat, lon)
    place = {"address": address}
    return place
