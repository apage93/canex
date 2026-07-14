"""Game domain model."""

import random
from typing import Optional

from app.core.config import settings
from app.models.player import Player
from app.core.exceptions import (
    GameAlreadyStartedError,
    GameFullError,
    GameNotInProgressError,
    NotEnoughPlayersError,
    NotHostError,
    NotYourTurnError,
)

# ── Board definition ──────────────────────────────────────────────────────────

BOARD: list[dict] = [
    {"id": 0,  "type": "go",       "name": "GO",                  "price": None, "rent": None, "color": None},
    {"id": 1,  "type": "property", "name": "Mediterranean Ave",    "price": 60,   "rent": 2,    "color": "purple"},
    {"id": 2,  "type": "empty",    "name": "Community Chest",      "price": None, "rent": None, "color": None},
    {"id": 3,  "type": "property", "name": "Baltic Ave",           "price": 60,   "rent": 4,    "color": "purple"},
    {"id": 4,  "type": "empty",    "name": "Income Tax",           "price": None, "rent": None, "color": None},
    {"id": 5,  "type": "property", "name": "Reading Railroad",     "price": 200,  "rent": 25,   "color": "railroad"},
    {"id": 6,  "type": "empty",    "name": "Jail / Visit",         "price": None, "rent": None, "color": None},
    {"id": 7,  "type": "property", "name": "Oriental Ave",         "price": 100,  "rent": 6,    "color": "lightblue"},
    {"id": 8,  "type": "empty",    "name": "Chance",               "price": None, "rent": None, "color": None},
    {"id": 9,  "type": "property", "name": "Vermont Ave",          "price": 100,  "rent": 6,    "color": "lightblue"},
    {"id": 10, "type": "property", "name": "Connecticut Ave",      "price": 120,  "rent": 8,    "color": "lightblue"},
    {"id": 11, "type": "property", "name": "St. Charles Place",    "price": 140,  "rent": 10,   "color": "pink"},
    {"id": 12, "type": "empty",    "name": "Free Parking",         "price": None, "rent": None, "color": None},
    {"id": 13, "type": "property", "name": "Kentucky Ave",         "price": 220,  "rent": 18,   "color": "red"},
    {"id": 14, "type": "empty",    "name": "Chance",               "price": None, "rent": None, "color": None},
    {"id": 15, "type": "property", "name": "Indiana Ave",          "price": 220,  "rent": 18,   "color": "red"},
    {"id": 16, "type": "property", "name": "Illinois Ave",         "price": 240,  "rent": 20,   "color": "red"},
    {"id": 17, "type": "property", "name": "B&O Railroad",         "price": 200,  "rent": 25,   "color": "railroad"},
    {"id": 18, "type": "empty",    "name": "Go to Jail",           "price": None, "rent": None, "color": None},
    {"id": 19, "type": "property", "name": "Pacific Ave",          "price": 300,  "rent": 26,   "color": "green"},
    {"id": 20, "type": "property", "name": "N. Carolina Ave",      "price": 300,  "rent": 26,   "color": "green"},
    {"id": 21, "type": "empty",    "name": "Community Chest",      "price": None, "rent": None, "color": None},
    {"id": 22, "type": "property", "name": "Pennsylvania Ave",     "price": 320,  "rent": 28,   "color": "green"},
    {"id": 23, "type": "property", "name": "Short Line Railroad",  "price": 200,  "rent": 25,   "color": "railroad"},
]

BOARD_SIZE: int = len(BOARD)



# ── Game ──────────────────────────────────────────────────────────────────────

class Game:
    def __init__(
        self, game_id: str, join_code: str, host_id: str, host_name: str
    ) -> None:
        self.game_id = game_id
        self.join_code = join_code
        self.status: str = "waiting"          # waiting | playing | finished
        self.players: list[Player] = []
        self.current_player_index: int = 0
        self.property_owners: dict[int, str] = {}  # square_id → player_id
        self.last_action: str = "Waiting for players to join…"
        self.winner: Optional[str] = None

        host = Player(host_id, host_name, is_host=True)
        self.players.append(host)

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
        # Should not happen because of the front but just in case..
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

        # Detect wrap-around (passing or landing on GO)
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
        self._check_winner_or_advance()

    # ── Private helpers ────────────────────────────────────────────────────────

    def _handle_property(self, current: Player, square: dict, msg: str) -> str:
        pos = square["id"]
        owner_id = self.property_owners.get(pos)

        if owner_id is None:
            # Unowned — buy automatically if affordable
            if current.money >= square["price"]:
                current.money -= square["price"]
                current.properties.append(pos)
                self.property_owners[pos] = current.id
                msg += f" → purchased for ${square['price']}"
            else:
                msg += f" → couldn't afford ${square['price']} (skipped)"

        elif owner_id == current.id:
            msg += " → own property, nothing happens"

        else:
            owner = self._find_player(owner_id)
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

    def _check_winner_or_advance(self) -> None:
        active = [p for p in self.players if not p.is_bankrupt]
        if len(active) == 1:
            self.winner = active[0].name
            self.status = "finished"
            self.last_action += f"  🏆 {self.winner} wins!"
        else:
            self._advance_turn()

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

    def _find_player(self, player_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.id == player_id), None)

    # ── Serialisation ──────────────────────────────────────────────────────────

    def check_last_player_wins(self) -> bool:
        """If only one non-bankrupt player remains, declare them the winner.

        Returns True if a winner was just crowned, False otherwise.
        """
        if self.status != "playing":
            return False
        active = [p for p in self.players if not p.is_bankrupt]
        if len(active) == 1:
            self.winner = active[0].name
            self.status = "finished"
            self.last_action = f"🏆 {self.winner} wins by default!"
            return True
        return False

    def get_player(self, player_id: str) -> Optional[Player]:
        return self._find_player(player_id)

    def to_dict(self) -> dict:
        return {
            "game_id": self.game_id,
            "join_code": self.join_code,
            "status": self.status,
            "players": [p.to_dict() for p in self.players],
            "current_player_index": self.current_player_index,
            "property_owners": {str(k): v for k, v in self.property_owners.items()},
            "board": BOARD,
            "last_action": self.last_action,
            "winner": self.winner,
        }

