import random
from typing import Optional

BOARD = [
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

BOARD_SIZE = len(BOARD)
STARTING_MONEY = 1500
GO_SALARY = 200


class Player:
    def __init__(self, player_id: str, name: str, is_host: bool = False):
        self.id = player_id
        self.name = name
        self.money = STARTING_MONEY
        self.position = 0
        self.properties: list[int] = []
        self.is_bankrupt = False
        self.is_host = is_host

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "money": self.money,
            "position": self.position,
            "properties": self.properties,
            "is_bankrupt": self.is_bankrupt,
            "is_host": self.is_host,
        }


class Game:
    def __init__(self, game_id: str, join_code: str, host_id: str, host_name: str):
        self.game_id = game_id
        self.join_code = join_code
        self.status = "waiting"  # waiting | playing | finished
        self.players: list[Player] = []
        self.current_player_index = 0
        self.property_owners: dict[int, str] = {}  # square_id -> player_id
        self.last_action = "Waiting for players to join..."
        self.winner: Optional[str] = None

        host = Player(host_id, host_name, is_host=True)
        self.players.append(host)

    # ── Lobby ─────────────────────────────────────────────────────────────────

    def add_player(self, player_id: str, name: str) -> Player:
        if self.status != "waiting":
            raise ValueError("Game has already started")
        if len(self.players) >= 4:
            raise ValueError("Game is full (max 4 players)")
        player = Player(player_id, name)
        self.players.append(player)
        return player

    def start(self, requesting_player_id: str) -> None:
        host = next((p for p in self.players if p.is_host), None)
        if not host or host.id != requesting_player_id:
            raise ValueError("Only the host can start the game")
        if len(self.players) < 2:
            raise ValueError("Need at least 2 players to start")
        random.shuffle(self.players)
        self.status = "playing"
        self.current_player_index = 0
        self.last_action = f"Game started! {self.players[0].name} goes first."

    # ── Gameplay ───────────────────────────────────────────────────────────────

    def roll_and_play(self, requesting_player_id: str) -> None:
        if self.status != "playing":
            raise ValueError("Game is not currently in progress")

        current = self.players[self.current_player_index]
        if current.id != requesting_player_id:
            raise ValueError("It is not your turn")

        dice = random.randint(1, 6)
        old_pos = current.position
        new_pos = (old_pos + dice) % BOARD_SIZE

        passed_go = new_pos < old_pos  # wrapped around the board
        if passed_go:
            current.money += GO_SALARY

        current.position = new_pos
        square = BOARD[new_pos]

        msg = f"{current.name} rolled {dice} → landed on {square['name']}"
        if passed_go:
            msg += f" (passed GO, collected ${GO_SALARY})"

        if square["type"] == "property":
            owner_id = self.property_owners.get(new_pos)

            if owner_id is None:
                # Unowned — buy automatically if affordable
                if current.money >= square["price"]:
                    current.money -= square["price"]
                    current.properties.append(new_pos)
                    self.property_owners[new_pos] = current.id
                    msg += f" → purchased for ${square['price']}"
                else:
                    msg += f" → couldn't afford ${square['price']} (skipped)"

            elif owner_id == current.id:
                msg += " → own property, nothing happens"

            else:
                owner = next((p for p in self.players if p.id == owner_id), None)
                if owner and not owner.is_bankrupt:
                    rent = square["rent"]
                    if current.money >= rent:
                        current.money -= rent
                        owner.money += rent
                        msg += f" → paid ${rent} rent to {owner.name}"
                    else:
                        msg += f" → {current.name} can't pay ${rent} rent to {owner.name} — BANKRUPT!"
                        self._declare_bankruptcy(current, owner)

        self.last_action = msg

        # Check for a winner
        active = [p for p in self.players if not p.is_bankrupt]
        if len(active) == 1:
            self.winner = active[0].name
            self.status = "finished"
            self.last_action += f" 🏆 {self.winner} wins!"
        else:
            self._advance_turn()

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _declare_bankruptcy(self, bankrupt: Player, creditor: Player) -> None:
        bankrupt.is_bankrupt = True
        for prop_id in bankrupt.properties:
            self.property_owners[prop_id] = creditor.id
            if prop_id not in creditor.properties:
                creditor.properties.append(prop_id)
        bankrupt.properties = []
        creditor.money += bankrupt.money
        bankrupt.money = 0

    def _advance_turn(self) -> None:
        active_indices = [i for i, p in enumerate(self.players) if not p.is_bankrupt]
        if not active_indices:
            return
        # Find the next active player after the current one (with wraparound)
        next_idx = next((i for i in active_indices if i > self.current_player_index), None)
        self.current_player_index = next_idx if next_idx is not None else active_indices[0]

    # ── Serialisation ──────────────────────────────────────────────────────────

    def get_player(self, player_id: str) -> Optional[Player]:
        return next((p for p in self.players if p.id == player_id), None)

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

