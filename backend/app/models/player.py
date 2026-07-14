"""Player domain model."""

from app.core.config import settings


class Player:
    def __init__(self, player_id: str, name: str, *, is_host: bool = False) -> None:
        self.id = player_id
        self.name = name
        self.money: int = settings.STARTING_MONEY
        self.position: int = 0
        self.properties: list[int] = []
        self.is_bankrupt: bool = False
        self.has_quit: bool = False
        self.is_host: bool = is_host

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "money": self.money,
            "position": self.position,
            "properties": self.properties,
            "is_bankrupt": self.is_bankrupt,
            "has_quit": self.has_quit,
            "is_host": self.is_host,
        }

