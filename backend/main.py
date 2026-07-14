"""Application factory.

Responsibilities kept intentionally minimal:
  • Create the FastAPI app
  • Register lifecycle hooks (lifespan)
  • Mount middleware
  • Register exception handlers
  • Include app.routers

Everything else lives in its own module.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from exceptions import GameNotFoundError, MonopolyError
from app.api.routes import games as games_router
from app.api.routes import ws as ws_router
from app.services.connection_manager import ConnectionManager
from app.services.game_store import GameStore


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise shared singletons on startup; clean up on shutdown."""
    app.state.store = GameStore()
    app.state.manager = ConnectionManager()
    yield
    # Future: flush persistent store, close DB connections, etc.


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Monopoly API",
        description="Real-time multiplayer Monopoly — FastAPI + WebSocket",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    @app.exception_handler(GameNotFoundError)
    async def game_not_found_handler(
        request: Request, exc: GameNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MonopolyError)
    async def monopoly_error_handler(
        request: Request, exc: MonopolyError
    ) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(games_router.router)
    app.include_router(ws_router.router)

    return app


app = create_app()

