"""GameStore — repository for in-memory game state.

Abstracting storage behind this class means the rest of the codebase
never touches a raw dict. Swapping to Redis or a database only requires
replacing this file.
"""

import random
import string
import uuid

from app.core.config import settings
from exceptions import GameNotFoundError
from app.models.game import Game


class GameStore:
    def __init__(self) -> None:
        self._games: dict[str, Game] = {}

    # ── Write ──────────────────────────────────────────────────────────────────

    def create_game(self, host_id: str, host_name: str) -> Game:
        """Instantiate a Game with a collision-free join code and persist it."""
        game_id = str(uuid.uuid4())
        join_code = self._unique_code()
        game = Game(game_id, join_code, host_id, host_name)
        self._games[game_id] = game
        return game

    # ── Read ───────────────────────────────────────────────────────────────────

    def get(self, game_id: str) -> Game:
        """Return the game or raise GameNotFoundError."""
        game = self._games.get(game_id)
        if game is None:
            raise GameNotFoundError(game_id)
        return game

    def list_waiting(self) -> list[Game]:
        """Return all games currently in 'waiting' status."""
        return [g for g in self._games.values() if g.status == "waiting"]

    def get_by_code(self, join_code: str) -> Game:
        """Case-insensitive lookup by join code."""
        code = join_code.upper()
        game = next(
            (g for g in self._games.values() if g.join_code == code), None
        )
        if game is None:
            raise GameNotFoundError(join_code)
        return game

    # ── Private ────────────────────────────────────────────────────────────────

    def _unique_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        existing = {g.join_code for g in self._games.values()}
        while True:
            code = "".join(
                random.choices(alphabet, k=settings.JOIN_CODE_LENGTH)
            )
            if code not in existing:
                return code

