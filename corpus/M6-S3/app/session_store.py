import uuid
from typing import Dict

# session_id -> user_id
SESSIONS: Dict[str, int] = {}

# session_id -> {product_id: quantity}
CARTS: Dict[str, Dict[int, int]] = {}


def create_session(user_id: int) -> str:
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = user_id
    if session_id not in CARTS:
        CARTS[session_id] = {}
    return session_id


def destroy_session(session_id: str):
    SESSIONS.pop(session_id, None)
    CARTS.pop(session_id, None)
