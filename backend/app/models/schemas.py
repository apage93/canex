"""Pydantic schemas for API request validation and response serialisation.

Keeping these separate from the domain model means:
- The domain is not polluted with transport concerns.
- API contracts can evolve independently of internal representation.
- Field-level validation (min/max length, etc.) is explicit and colocated.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class CreateGameRequest(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=20)


class JoinGameRequest(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=20)


# ── Responses ─────────────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    """Returned after creating or joining a game."""
    game_id: str
    join_code: str
    player_id: str
    player_name: str


class SquareOut(BaseModel):
    id: int
    type: Literal["go", "property", "empty"]
    name: str
    price: Optional[int] = None
    rent: Optional[int] = None
    color: Optional[str] = None


class PlayerOut(BaseModel):
    id: str
    name: str
    money: int
    position: int
    properties: list[int]
    is_bankrupt: bool
    is_host: bool


class GameStateOut(BaseModel):
    game_id: str
    join_code: str
    status: Literal["waiting", "playing", "finished"]
    players: list[PlayerOut]
    current_player_index: int
    property_owners: dict[str, str]
    board: list[SquareOut]
    last_action: str
    winner: Optional[str] = None

