"""Board definition — static data, never changes at runtime."""

from typing import Literal, TypedDict


class Square(TypedDict):
    id: int
    type: Literal["go", "property", "empty"]
    name: str
    price: int | None
    rent: int | None
    color: str | None


BOARD: list[Square] = [
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

