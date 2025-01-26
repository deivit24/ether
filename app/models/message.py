from typing import Optional, Any, Tuple
from datetime import datetime, UTC, timedelta

from fastapi import HTTPException
from geoalchemy2.shape import to_shape

from pydantic import BaseModel, root_validator, model_validator
from sqlmodel import Field, SQLModel, Column
from geoalchemy2 import Geometry
from starlette import status

MAX_CONTENT_LENGTH = 140
DAY_IN_SECONDS = 60 * 60 * 24
FIVE_MINUTES_IN_SECONDS = 60 * 5

class MessageBase(SQLModel):
    content: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delete_after: datetime = Field(default_factory=lambda: datetime.now(UTC))
    location: Any = Field(sa_column=Column(Geometry('POINT')))
    ip_address: str
    address: str

    class Config:
        # Allow arbitrary types like Geometry
        arbitrary_types_allowed = True

    @property
    def coordinates(self) -> Optional[Tuple[float, float]]:
        """Extract (lon, lat) coordinates from the geometry field."""
        if self.location:
            point = to_shape(self.location)  # Convert WKBElement to Shapely Point
            return point.x, point.y  # Return coordinates as a tuple
        return None

    @property
    def user(self) -> str:
        if ":" in self.ip_address:  # Check if the input is a MAC address
            segments = self.ip_address.split(":")
            # Convert each segment to an integer using base 16 (hexadecimal)
            numbers = [int(segment, 16) for segment in segments if segment]
        else:  # Assume it's an IPv4 address
            segments = self.ip_address.split(".")
            # Convert each segment to an integer
            numbers = [int(segment) for segment in segments]

        # Calculate the unique number
        unique_number = sum(numbers)
        return f"anon-{unique_number}"


    # Pydantic model to accept message content
class MessageCreate(BaseModel):
    content: str
    delete_after_seconds: int
    lat: float
    lon: float

    @model_validator(mode='after')
    def check_content_length(self):
        if len(self.content) > MAX_CONTENT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Content length exceeds the limit of {MAX_CONTENT_LENGTH} characters"
            )
        if not (FIVE_MINUTES_IN_SECONDS < self.delete_after_seconds <= DAY_IN_SECONDS):
            HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="delete_after_seconds must be greater than zero"
            )

        return self

    class Config:
        # Allow arbitrary types like Geometry in the BaseModel
        arbitrary_types_allowed = True



class Message(MessageBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


# Response model to avoid WKBElement serialization issues
class MessageResponse(BaseModel):
    id: int
    content: Optional[str]
    created_at: datetime
    delete_after: datetime
    # ip_address: str
    address: str
    user: str
    # coordinates: Optional[Tuple[float, float]]  # Serialized coordinat


class LocationResponse(BaseModel):
    address: str

class LocationSearchResponse(BaseModel):
    address: str
    latitude: float
    longitude: float