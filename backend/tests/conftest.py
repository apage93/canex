"""Shared pytest fixtures."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import create_app
from models.game import Game
from services.game_store import GameStore


# ── App / HTTP client ─────────────────────────────────────────────────────────

@pytest.fixture
def app():
    """Fresh FastAPI app instance per test (isolated store & manager)."""
    return create_app()


@pytest.fixture
def client(app):
    """Synchronous TestClient that also supports WebSocket."""
    with TestClient(app) as c:
        yield c


# ── Domain helpers ────────────────────────────────────────────────────────────

@pytest.fixture
def two_player_game() -> Game:
    game = Game("game-1", "ABCDEF", "host-id", "Alice")
    game.add_player("p2-id", "Bob")
    return game


@pytest.fixture
def started_game(two_player_game: Game) -> Game:
    """Two-player game with deterministic player order (no shuffle)."""
    with patch("models.game.random.shuffle"):
        two_player_game.start("host-id")
    # players[0] = Alice (host), players[1] = Bob
    return two_player_game

