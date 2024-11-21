from typing import Optional, List

from fastapi import APIRouter, Request, Query
from sqlalchemy import delete
from datetime import datetime, UTC
from app.api.deps import SessionDep, get_db
from app.crud import get_nearby_messages, create_ether_message
from app.models.message import MessageCreate, MessageResponse, Message

router = APIRouter()

@router.get("/", response_model=List[MessageResponse])
def get_messages(
    session: SessionDep,
    lat: float = Query(...),
    lon: float = Query(...),
    radius: Optional[float] = Query(5000.0, gt=0),
):
    messages = get_nearby_messages(session, lat, lon, radius)
    return messages


@router.post("/", response_model=MessageResponse)
async def create_message(request: Request, session:SessionDep,  message: MessageCreate):
    """
    Create a new message with the client IP and store it in the database.
    """
    client_ip = request.client.host  # Extract client IP from the request
    for header in request.headers.raw:
        print(header)
    db_message = create_ether_message(session, message, client_ip)
    return db_message


def delete_expired_messages():
    db_generator = get_db()  # This returns a generator object
    session = next(db_generator)
    try:
        current_time = datetime.now(UTC)
        # Create the query to find expired messages
        statement = delete(Message).where(
            Message.delete_after <= current_time
        )

        # Execute the statement and commit changes
        result = session.exec(statement=statement)
        session.commit()
        print(f"Deleted messages: {result.rowcount}")  # Log the number of deleted messages

    finally:
        # Close the session
        db_generator.close()


