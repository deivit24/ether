from typing import Optional, List
from datetime import datetime, UTC, timedelta
from sqlalchemy import func
from sqlmodel import Session, select

from app.core.security import get_password_hash
from app.models.message import Message, MessageCreate
from app.models.user import User, UserCreate



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
        radius: Optional[float] = 5000.0
) -> List[Message]:
    """
    Retrieve messages within a specified radius using PostGIS spatial query.
    """
    # Define the current time in UTC
    current_time = datetime.now(UTC)
    # Create the query to find nearby messages
    statement = select(Message).where(
        func.ST_DWithin(
            Message.location,
            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
            radius,
            True  # Use sphere-based distance calculation
        ),
        Message.delete_after >= current_time
    )

    # Execute the query and extract the message objects
    results = session.execute(statement).all()
    messages = [message[0] for message in results]

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
    db_message = Message(
        content=message.content,
        created_at=created_at,
        delete_after=delete_at.astimezone(UTC),
        location=func.ST_SetSRID(func.ST_MakePoint(message.lon, message.lat), 4326),
        ip_address=client_ip,
    )

    # Add and commit the message to the database
    session.add(db_message)
    session.commit()
    session.refresh(db_message)

    return db_message