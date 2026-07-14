"""REST endpoints for game management."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import ManagerDep, StoreDep
from app.core.exceptions import (
    GameAlreadyStartedError,
    GameFullError,
    GameNotFoundError,
)
from app.models.schemas import (
    CreateGameRequest,
    GameStateOut,
    JoinGameRequest,
    LobbyGameOut,
    SessionResponse,
)

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("", response_model=list[LobbyGameOut])
async def list_games(
    store: StoreDep,
) -> list[LobbyGameOut]:
    """Return all games currently waiting for players."""
    return [
        LobbyGameOut(
            game_id=g.game_id,
            join_code=g.join_code,
            player_count=len(g.players),
            host_name=next(p.name for p in g.players if p.is_host),
        )
        for g in store.list_waiting()
    ]


@router.post("", response_model=SessionResponse, status_code=201)
async def create_game(
    body: CreateGameRequest,
    store: StoreDep,
) -> SessionResponse:
    """Create a new game. The creator automatically becomes the host."""
    host_id = str(uuid.uuid4())
    game = store.create_game(host_id, body.player_name)
    return SessionResponse(
        game_id=game.game_id,
        join_code=game.join_code,
        player_id=host_id,
        player_name=body.player_name,
    )


@router.post("/join", response_model=SessionResponse, status_code=200)
async def join_game(
    body: JoinGameRequest,
    code: Annotated[str, Query(min_length=1)],
    store: StoreDep,
    manager: ManagerDep,
) -> SessionResponse:
    """Join an existing game by its join code."""
    try:
        game = store.get_by_code(code)
    except GameNotFoundError:
        raise HTTPException(status_code=404, detail="No game found with this code")

    player_id = str(uuid.uuid4())

    try:
        game.add_player(player_id, body.player_name)
    except GameAlreadyStartedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except GameFullError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Notify existing players of the new arrival
    await manager.broadcast_state(game.game_id, game.to_dict())

    return SessionResponse(
        game_id=game.game_id,
        join_code=game.join_code,
        player_id=player_id,
        player_name=body.player_name,
    )


@router.get("/{game_id}", response_model=GameStateOut)
async def get_game_state(
    game_id: str,
    store: StoreDep,
) -> dict:
    """Return the current state of a game (useful for debugging / reconnection)."""
    try:
        game = store.get(game_id)
    except GameNotFoundError:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.to_dict()
