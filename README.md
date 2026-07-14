# 🎲 Monopoly — Web Multiplayer

A simplified Monopoly game playable in the browser, with real-time multiplayer via WebSockets.

- **Backend**: Python 3.14 · FastAPI · Uvicorn · Starlette
- **Frontend**: React 18 · TypeScript · Vite

---

## Rules implemented

| Rule | Detail |
|---|---|
| **Board** | 24 squares arranged in a loop (GO + properties + empty squares) |
| **Starting money** | $1 500 per player |
| **GO salary** | $200 collected every time a player passes or lands on GO |
| **Dice** | 1 six-sided die per turn |
| **Buy** | Landing on an unowned property → bought automatically if affordable |
| **Rent** | Landing on an opponent's property → rent paid to the owner |
| **Bankruptcy** | Can't pay rent → bankrupt; properties transferred to creditor |
| **Player quit** | Leaving mid-game → marked as out; last player standing wins by default |
| **Win condition** | Last non-bankrupt player standing |

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | ≥ 3.14 |
| Node.js | ≥ 18 |
| npm | ≥ 9 |

---

## Quick start

### 1 — Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API is now live at <http://localhost:8000>.  
Interactive docs: <http://localhost:8000/docs>

### 2 — Frontend

Open a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

The app is now available at <http://localhost:5173>.

> Vite automatically proxies `/api/*` requests (including WebSockets) to `http://localhost:8000`, so no CORS configuration is needed during development.

### 3 — Tests

```bash
cd backend
python -m pytest tests/ -v
```

Run with coverage:

```bash
python -m pytest tests/ --cov=app --cov=main --cov-report=term-missing
```

---

## Test coverage

> 73 tests · **92% overall coverage**

| Module | Stmts | Cover |
|---|---|---|
| `app/api/dependencies.py` | 11 | **100%** |
| `app/api/routes/games.py` | 41 | 95% |
| `app/core/config.py` | 8 | **100%** |
| `app/core/exceptions.py` | 27 | 93% |
| `app/models/board.py` | 4 | **100%** |
| `app/models/player.py` | 13 | **100%** |
| `app/models/game.py` | 112 | 96% |
| `app/models/schemas.py` | 15 | **100%** |
| `app/services/connection_manager.py` | 25 | 88% |
| `app/services/game_store.py` | 35 | **97%** |
| `app/api/routes/ws.py` | 68 | 82% |
| `main.py` | 28 | 93% |
| **Total** | **387** | **93%** |

The WebSocket route (`ws.py`) has the lowest coverage (82%) because the leave/disconnect paths are harder to exercise in the test client — they are covered by integration tests but not every branch combination.

---

## How to play

1. **Create a game** — Enter your name and click *Create Game*.
2. **Share** — Copy the 6-character join code or the invite link and send it to friends (2–4 players).
3. **Join** — Each other player opens the link or enters the code manually on the lobby page.
4. **Start** — The host clicks *🚀 Start Game* once at least 2 players have joined. The button grows and glows green when ready.
5. **Take turns** — Click **🎲 Roll Dice** when it's your turn. The action log keeps everyone informed.
6. **Win** — Be the last player standing!

> **Note:** The *Join Game* tab is disabled when no game is currently waiting — it enables automatically once a game is created.

---

## Project structure

```
canex/
├── backend/
│   ├── main.py                        # App factory — lifespan, middleware, routers
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py        # Annotated dependency aliases (StoreDep, ManagerDep)
│   │   │   └── routes/
│   │   │       ├── games.py           # REST endpoints (board, create, join, list, get)
│   │   │       └── ws.py              # WebSocket endpoint + message dispatch
│   │   ├── core/
│   │   │   ├── config.py              # Centralised game settings (money, board size, limits)
│   │   │   └── exceptions.py          # Typed domain exceptions
│   │   ├── models/
│   │   │   ├── board.py               # Static board definition (TypedDict Square + BOARD)
│   │   │   ├── player.py              # Player domain model
│   │   │   ├── game.py                # Game domain model + business rules
│   │   │   └── schemas.py             # Pydantic schemas (request/response)
│   │   └── services/
│   │       ├── game_store.py          # In-memory game repository
│   │       └── connection_manager.py  # WebSocket room management
│   └── tests/
│       ├── conftest.py
│       ├── test_game.py
│       ├── test_game_store.py
│       └── test_api.py
└── frontend/
    ├── src/
    │   ├── App.tsx                    # Root — session management, routing
    │   ├── types.ts                   # Shared TypeScript interfaces
    │   ├── hooks/
    │   │   └── useGameWebSocket.ts    # WS hook (connect, reconnect, send)
    │   └── components/
    │       ├── LobbyPage.tsx          # Create / Join forms
    │       ├── GamePage.tsx           # Waiting room + playing + end screen
    │       ├── Board.tsx              # CSS-grid board
    │       └── PlayerCard.tsx         # Per-player status card
    ├── package.json
    └── vite.config.ts
```

---

## Architecture notes

- **State is in-memory** on the server — restarting the backend clears all games. A production version would use Redis or a database.
- **WebSocket broadcast** — every player action triggers a full state push to all connected clients in that game room.
- **Board served separately** — `GET /api/games/board` returns the static board once; it is no longer included in every WebSocket state update, reducing payload size.
- **Reconnection** — the WS hook auto-retries every 2 s on network drops; session info (`game_id` + `player_id`) is stored in `sessionStorage` (tab-scoped) so a page refresh reconnects seamlessly.
- **Join codes** — generated with `secrets.choice` (CSPRNG), giving ~2.2 billion combinations for a 6-character alphanumeric code.
- **Dependency injection** — FastAPI dependencies use the `Annotated` pattern (`StoreDep`, `ManagerDep`) defined once in `app/api/dependencies.py`.
- **Typed status** — game status uses `Literal["waiting", "playing", "finished"]` throughout, caught at type-check time rather than at runtime.
- **No auth** — player identity is a UUID assigned at join time. A production version would add proper authentication.

````
This is the description of what the code block changes:
<changeDescription>
Update project structure, coverage table and architecture notes to reflect latest changes
</changeDescription>

This is the code block that represents the suggested code change:
````markdown
// ...existing code...
| `app/api/dependencies.py` | 11 | **100%** |
| `app/api/routes/games.py` | 41 | 95% |
| `app/core/config.py` | 8 | **100%** |
| `app/core/exceptions.py` | 27 | 93% |
| `app/models/board.py` | 4 | **100%** |
| `app/models/player.py` | 13 | **100%** |
| `app/models/game.py` | 112 | 96% |
| `app/models/schemas.py` | 15 | **100%** |
| `app/services/connection_manager.py` | 25 | 88% |
| `app/services/game_store.py` | 35 | **97%** |
| `app/api/routes/ws.py` | 68 | 82% |
| `main.py` | 28 | 93% |
| **Total** | **387** | **93%** |
// ...existing code...
## Project structure

```
canex/
├── backend/
│   ├── main.py                        # App factory — lifespan, middleware, routers
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py        # Annotated dependency aliases (StoreDep, ManagerDep)
│   │   │   └── routes/
│   │   │       ├── games.py           # REST endpoints (board, create, join, list, get)
│   │   │       └── ws.py              # WebSocket endpoint + message dispatch
│   │   ├── core/
│   │   │   ├── config.py              # Centralised game settings (money, board size, limits)
│   │   │   └── exceptions.py          # Typed domain exceptions
│   │   ├── models/
│   │   │   ├── board.py               # Static board definition (TypedDict Square + BOARD)
│   │   │   ├── player.py              # Player domain model
│   │   │   ├── game.py                # Game domain model + business rules
│   │   │   └── schemas.py             # Pydantic schemas (request/response)
│   │   └── services/
│   │       ├── game_store.py          # In-memory game repository
│   │       └── connection_manager.py  # WebSocket room management
│   └── tests/
│       ├── conftest.py
│       ├── test_game.py
│       ├── test_game_store.py
│       └── test_api.py
└── frontend/
    ├── src/
    │   ├── App.tsx                    # Root — session management, routing
    │   ├── types.ts                   # Shared TypeScript interfaces
    │   ├── hooks/
    │   │   └── useGameWebSocket.ts    # WS hook (connect, reconnect, send)
    │   └── components/
    │       ├── LobbyPage.tsx          # Create / Join forms
    │       ├── GamePage.tsx           # Waiting room + playing + end screen
    │       ├── Board.tsx              # CSS-grid board
    │       └── PlayerCard.tsx         # Per-player status card
    ├── package.json
    └── vite.config.ts
```

---

## Architecture notes

- **State is in-memory** on the server — restarting the backend clears all games. A production version would use Redis or a database.
- **WebSocket broadcast** — every player action triggers a full state push to all connected clients in that game room.
- **Board served separately** — `GET /api/games/board` returns the static board once; it is no longer included in every WebSocket state update, reducing payload size.
- **Reconnection** — the WS hook auto-retries every 2 s on network drops; session info (`game_id` + `player_id`) is stored in `sessionStorage` (tab-scoped) so a page refresh reconnects seamlessly.
- **Join codes** — generated with `secrets.choice` (CSPRNG), giving ~2.2 billion combinations for a 6-character alphanumeric code.
- **Dependency injection** — FastAPI dependencies use the `Annotated` pattern (`StoreDep`, `ManagerDep`) defined once in `app/api/dependencies.py`.
- **Typed status** — game status uses `Literal["waiting", "playing", "finished"]` throughout, caught at type-check time rather than at runtime.
- **No auth** — player identity is a UUID assigned at join time. A production version would add proper authentication.

````
<userPrompt>
Provide the fully rewritten file, incorporating the suggested code change. You must produce the complete file.
</userPrompt>

