"""FastAPI dependency providers.

Both singletons live on app.state, initialised during the lifespan in
main.py.

We type-hint against `HTTPConnection` (the common Starlette base class for
both `Request` and `WebSocket`) so the same dependency functions work in
HTTP *and* WebSocket endpoints without any duplication.
"""

from starlette.requests import HTTPConnection

from app.services.connection_manager import ConnectionManager
from app.services.game_store import GameStore


def get_store(conn: HTTPConnection) -> GameStore:
    return conn.app.state.store  # type: ignore[no-any-return]


def get_manager(conn: HTTPConnection) -> ConnectionManager:
    return conn.app.state.manager  # type: ignore[no-any-return]

