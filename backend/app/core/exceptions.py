"""Domain-level exceptions.

Raising typed exceptions in the domain layer lets the HTTP / WebSocket
layer convert them to the right status codes without leaking transport
concerns into business logic.
"""


class MonopolyError(Exception):
    """Base class for all domain errors."""


class GameNotFoundError(MonopolyError):
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Game not found: {identifier!r}")


class PlayerNotFoundError(MonopolyError):
    def __init__(self, player_id: str) -> None:
        self.player_id = player_id
        super().__init__(f"Player not found: {player_id!r}")


class GameAlreadyStartedError(MonopolyError):
    def __init__(self) -> None:
        super().__init__("The game has already started")


class GameFullError(MonopolyError):
    def __init__(self) -> None:
        super().__init__("The game is full (max 4 players)")


class NotYourTurnError(MonopolyError):
    def __init__(self) -> None:
        super().__init__("It is not your turn")


class GameNotInProgressError(MonopolyError):
    def __init__(self) -> None:
        super().__init__("The game is not currently in progress")


class NotEnoughPlayersError(MonopolyError):
    def __init__(self, needed: int) -> None:
        super().__init__(f"Need at least {needed} players to start")


class NotHostError(MonopolyError):
    def __init__(self) -> None:
        super().__init__("Only the host can perform this action")

