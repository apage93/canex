# 🎲 Monopoly — Web Multiplayer

A simplified Monopoly game playable in the browser, with real-time multiplayer via WebSockets.

- **Backend**: Python 3.11 · FastAPI · Uvicorn
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
| **Win condition** | Last player standing |

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | ≥ 3.11 |
| Node.js | ≥ 18 |
| npm | ≥ 9 |

---

## Quick start

### 1 — Backend

```bash
cd backend
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

---

## How to play

1. **Create a game** — Enter your name and click *Create Game*.
2. **Share** — Copy the 6-character code or the join link and send it to your friends (2–4 players total).
3. **Join** — Each other player opens the link (or goes to the app and uses the code).
4. **Start** — The host clicks *Start Game* once everyone has joined.
5. **Take turns** — Click **🎲 Roll Dice** when it's your turn. The action log on the right keeps everyone informed.
6. **Win** — Be the last player standing!

---

## Project structure

```
canex/
├── backend/
│   ├── game.py          # Game logic (board, players, rules)
│   ├── main.py          # FastAPI app, REST + WebSocket endpoints
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.tsx                        # Root — session management, routing
    │   ├── types.ts                       # Shared TypeScript types
    │   ├── hooks/
    │   │   └── useGameWebSocket.ts        # WS hook (connect, reconnect, send)
    │   └── components/
    │       ├── LobbyPage.tsx              # Create / Join forms
    │       ├── GamePage.tsx               # Waiting room + playing screen
    │       ├── Board.tsx                  # 7×7 CSS-grid board
    │       └── PlayerCard.tsx             # Per-player status card
    ├── package.json
    └── vite.config.ts
```

---

## Architecture notes

- **State is in-memory** on the server — restarting the backend clears all games. A production version would use Redis or a database.
- **WebSocket broadcast** — every player action triggers a full state push to all connected clients in that game room.
- **Reconnection** — the WS hook auto-retries every 2 s on network drops; session info (game_id + player_id) is stored in `localStorage` so a page refresh reconnects the player seamlessly.
- **No auth** — player identity is a UUID assigned at join time. A production version would add proper authentication.

