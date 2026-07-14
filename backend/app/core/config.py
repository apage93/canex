"""Centralised application settings.

All game constants live here so changing a rule only requires touching
one file, without hunting through the codebase.
"""


class Settings:
    # ── Game rules ─────────────────────────────────────────────────────────────
    STARTING_MONEY: int = 1_500
    GO_SALARY: int = 200
    DIE_FACES: int = 6
    MAX_PLAYERS: int = 4
    MIN_PLAYERS_TO_START: int = 2

    # ── Infrastructure ─────────────────────────────────────────────────────────
    JOIN_CODE_LENGTH: int = 6


settings = Settings()

