from typing import List
from fastapi import APIRouter, Query
from app.crud import get_address, find_place
from app.models.message import LocationResponse, LocationSearchResponse

router = APIRouter()

@router.get("/", response_model=LocationResponse)
def get_location(
    lat: float = Query(...),
    lon: float = Query(...),
):
    address = get_address(lat, lon)
    place = {"address": address}
    return place

@router.get("/search", response_model=List[LocationSearchResponse])
def get_location(
    search: str = Query(...),
):
    locations = find_place(search)


    return locations
