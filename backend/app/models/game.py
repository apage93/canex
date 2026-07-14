"""Game domain model."""

import random
from typing import Literal

from app.core.config import settings
from app.models.board import BOARD, BOARD_SIZE, Square
from app.models.player import Player
from app.core.exceptions import (
    GameAlreadyStartedError,
    GameFullError,
    GameNotInProgressError,
    NotEnoughPlayersError,
    NotHostError,
    NotYourTurnError,
)

GameStatus = Literal["waiting", "playing", "finished"]


class Game:
    def __init__(
        self, game_id: str, join_code: str, host_id: str, host_name: str
    ) -> None:
        self.game_id = game_id
        self.join_code = join_code
        self.status: GameStatus = "waiting"
        self.players: list[Player] = []
        self.current_player_index: int = 0
        self.property_owners: dict[int, str] = {}  # square_id → player_id
        self.last_action: str = "Waiting for players to join…"
        self.winner: str | None = None

        self.players.append(Player(host_id, host_name, is_host=True))

    # ── Lobby ─────────────────────────────────────────────────────────────────

    def add_player(self, player_id: str, name: str) -> Player:
        if self.status != "waiting":
            raise GameAlreadyStartedError()
        if len(self.players) >= settings.MAX_PLAYERS:
            raise GameFullError()
        player = Player(player_id, name)
        self.players.append(player)
        return player

    def start(self, requesting_player_id: str) -> None:
        if not any(p.is_host and p.id == requesting_player_id for p in self.players):
            raise NotHostError()
        if len(self.players) < settings.MIN_PLAYERS_TO_START:
            raise NotEnoughPlayersError(settings.MIN_PLAYERS_TO_START)
        random.shuffle(self.players)
        self.status = "playing"
        self.current_player_index = 0
        self.last_action = f"Game started! {self.players[0].name} goes first."

    # ── Gameplay ───────────────────────────────────────────────────────────────

    def roll_and_play(self, requesting_player_id: str) -> None:
        if self.status != "playing":
            raise GameNotInProgressError()

        current = self.players[self.current_player_index]
        if current.id != requesting_player_id:
            raise NotYourTurnError()

        dice = random.randint(1, settings.DIE_FACES)
        old_pos = current.position
        new_pos = (old_pos + dice) % BOARD_SIZE

        passed_go = new_pos < old_pos
        if passed_go:
            current.money += settings.GO_SALARY

        current.position = new_pos
        square = BOARD[new_pos]

        msg = f"{current.name} rolled {dice} → {square['name']}"
        if passed_go:
            msg += f" (passed GO, collected ${settings.GO_SALARY})"

        if square["type"] == "property":
            msg = self._handle_property(current, square, msg)

        self.last_action = msg
        self._resolve_winner_or_advance()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _handle_property(self, current: Player, square: Square, msg: str) -> str:
        pos = square["id"]
        owner_id = self.property_owners.get(pos)

        if owner_id is None:
            if current.money >= square["price"]:
                current.money -= square["price"]
                current.properties.append(pos)
                self.property_owners[pos] = current.id
                msg += f" → purchased for ${square['price']}"
            else:
                msg += f" → couldn't afford ${square['price']} (skipped)"

        elif owner_id == current.id:
            msg += " �� own property, nothing happens"

        else:
            owner = self.get_player(owner_id)
            if owner and not owner.is_bankrupt:
                rent = square["rent"]
                if current.money >= rent:
                    current.money -= rent
                    owner.money += rent
                    msg += f" → paid ${rent} rent to {owner.name}"
                else:
                    msg += (
                        f" → {current.name} cannot pay ${rent} rent"
                        f" to {owner.name} — BANKRUPT!"
                    )
                    self._declare_bankruptcy(current, owner)

        return msg

    def _declare_bankruptcy(self, bankrupt: Player, creditor: Player) -> None:
        bankrupt.is_bankrupt = True
        for prop_id in bankrupt.properties:
            self.property_owners[prop_id] = creditor.id
            if prop_id not in creditor.properties:
                creditor.properties.append(prop_id)
        bankrupt.properties = []
        creditor.money += bankrupt.money
        bankrupt.money = 0

    def _resolve_winner_or_advance(self, *, default_win: bool = False) -> bool:
        """Check if only one active player remains and crown them winner.

        Returns True if the game just ended, False otherwise.
        Called after every roll and after a player quits.
        """
        active = [p for p in self.players if not p.is_bankrupt]
        if len(active) == 1:
            self.winner = active[0].name
            self.status = "finished"
            suffix = " wins by default!" if default_win else f"  🏆 {self.winner} wins!"
            self.last_action += suffix
            return True
        if not default_win:
            self._advance_turn()
        return False

    def _advance_turn(self) -> None:
        active_indices = [i for i, p in enumerate(self.players) if not p.is_bankrupt]
        if not active_indices:
            return
        next_idx = next(
            (i for i in active_indices if i > self.current_player_index), None
        )
        self.current_player_index = (
            next_idx if next_idx is not None else active_indices[0]
        )

    # ── Public API ───────────────────────────────────────────────────��─────────

    def check_last_player_wins(self) -> bool:
        """Declare winner by default if only one player remains. Returns True if crowned."""
        if self.status != "playing":
            return False
        return self._resolve_winner_or_advance(default_win=True)

    def get_player(self, player_id: str) -> Player | None:
        return next((p for p in self.players if p.id == player_id), None)

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "join_code": self.join_code,
            "status": self.status,
            "players": [p.to_dict() for p in self.players],
            "current_player_index": self.current_player_index,
            "property_owners": {str(k): v for k, v in self.property_owners.items()},
            "last_action": self.last_action,
            "winner": self.winner,
        }
