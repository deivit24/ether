import ipinfo

from typing import Optional, List
from datetime import datetime, UTC, timedelta

from geopy import Nominatim, Location
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from sqlalchemy import func, ScalarResult
from sqlmodel import Session, select, desc

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.message import Message, MessageCreate
from app.models.user import User, UserCreate

handler = ipinfo.getHandler(access_token=settings.IPINFO_API_KEY,cache_options={'ttl':30, 'maxsize': 128})

def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_nearby_messages(
        session: Session,
        lat: float,
        lon: float,
        radius: Optional[float] = 5000.0,
        limit: int = 10,
        offset: int = 0
) -> ScalarResult[Message]:
    """
    Retrieve messages within a specified radius using PostGIS spatial query.
    """
    # Define the current time in UTC
    current_time = datetime.now(UTC)
    # Create the query to find nearby messages
    statement = (select(Message).where(
        func.ST_DWithin(
            Message.location,
            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
            radius,
            True  # Use sphere-based distance calculation
        ),
        Message.delete_after >= current_time
    )
    .order_by(desc(Message.created_at))
    .limit(limit)
    .offset(offset)
    )

    # Execute the query and extract the message objects
    messages = session.scalars(statement)

    return messages


def create_ether_message(
        session: Session,
        message: MessageCreate,
        client_ip: str
) -> Message:
    """
    Create a new message and store it in the database.
    """
    # Build the message with the provided data
    created_at = datetime.now(UTC)
    delete_at = created_at + timedelta(seconds=message.delete_after_seconds)
    address = get_address(float(message.lat), float(message.lon))
    ip_location = get_location_from_ip()
    is_local = is_approximately_same_location(message.lat, message.lon, float(ip_location["latitude"]), float(ip_location["longitude"]))

    location = func.ST_SetSRID(func.ST_MakePoint(message.lon, message.lat), 4326)
    db_message = Message(
        content=message.content,
        created_at=created_at,
        delete_after=delete_at.astimezone(UTC),
        location=location,
        ip_address=client_ip,
        address=address,
        is_local=is_local
    )

    # Add and commit the message to the database
    session.add(db_message)
    session.commit()
    session.refresh(db_message)

    return db_message


def get_address(lat: float, lon: float) -> str:
    geolocator = Nominatim(user_agent="my_geocoder")
    try:
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language="en")
        place = "Unknown"
        if location:
            address = location.raw['address']
            city = address.get('city', address.get('town', address.get('village', None)))
            state = address.get('state', address.get('province', None))
            country = address.get('country', None)
            place = f"{city}, {state}, {country}"
        return place
    except ValueError:
        raise "Error: Invalid coordinate pair or location does not exist."
    except (GeocoderTimedOut, GeocoderServiceError):
        raise "Error: Geocoding service is unavailable. Please try again later."


def find_place(search: str) -> List[Location]:
    geolocator = Nominatim(user_agent="my_geocoder")
    try:
        locations = geolocator.geocode(query=search, exactly_one=False, language="en")
        if locations:
            return locations
        else:
            raise ValueError(f"No location found for {search}")
    except ValueError:
        raise f"Error: No location found for {search}"


def get_location_from_ip():
    details = handler.getDetails()
    return details.details


def is_approximately_same_location(lat1, lon1, lat2, lon2, tolerance=0.1):
    """
    Checks if two locations (lat1, lon1) and (lat2, lon2) are within a given tolerance.

    :param lat1: Latitude of first location
    :param lon1: Longitude of first location
    :param lat2: Latitude of second location
    :param lon2: Longitude of second location
    :param tolerance: Maximum allowed difference (default: 0.001)
    :return: True if both latitude and longitude differences are within tolerance, False otherwise
    """
    return abs(lat1 - lat2) <= tolerance and abs(lon1 - lon2) <= tolerance