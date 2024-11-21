from typing import Optional, Any, Tuple
from datetime import datetime, UTC, timedelta

from geoalchemy2.shape import to_shape

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Column
from geoalchemy2 import Geometry


class MessageBase(SQLModel):
    content: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delete_after: datetime = Field(default_factory=lambda: datetime.now(UTC))
    location: Any = Field(sa_column=Column(Geometry('POINT')))
    ip_address: str

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


    # Pydantic model to accept message content
class MessageCreate(BaseModel):
    content: str
    delete_after_seconds: int
    lat: float
    lon: float

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
    ip_address: str
    coordinates: Optional[Tuple[float, float]]  # Serialized coordinat