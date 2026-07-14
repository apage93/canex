"""ConnectionManager — WebSocket hub.

Centralises all WebSocket lifecycle management:
  • registering / removing connections
  • broadcasting state to an entire game room
  • sending targeted error messages

Using asyncio.gather for broadcasts means all sends happen concurrently
instead of sequentially, which matters when players are on slow connections.
"""

import asyncio
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # game_id → list of (player_id, WebSocket)
        self._rooms: dict[str, list[tuple[str, WebSocket]]] = {}

    # ── Connection lifecycle ───────────────────────────────────────────────────

    def connect(self, game_id: str, player_id: str, ws: WebSocket) -> None:
        self._rooms.setdefault(game_id, []).append((player_id, ws))

    def disconnect(self, game_id: str, ws: WebSocket) -> None:
        self._rooms[game_id] = [
            (pid, conn)
            for pid, conn in self._rooms.get(game_id, [])
            if conn is not ws
        ]

    # ── Broadcasting ──────────────────────────────────────────────────────────

    async def broadcast_state(self, game_id: str, state: dict) -> None:
        """Push the full game state to every connected player concurrently."""
        payload = {"type": "game_state", "state": state}
        await self._send_all(game_id, payload)

    async def send_error(self, ws: WebSocket, message: str) -> None:
        """Send an error message to a single connection."""
        try:
            await ws.send_json({"type": "error", "message": message})
        except Exception:
            pass  # Socket may already be closed

    # ── Private ────────────────────────────────────────────────────────────────

    async def _send_all(self, game_id: str, payload: dict) -> None:
        conns = self._rooms.get(game_id, [])
        if not conns:
            return

        results = await asyncio.gather(
            *(ws.send_json(payload) for _, ws in conns),
            return_exceptions=True,
        )

        # Prune dead connections
        dead = {
            ws
            for (_, ws), result in zip(conns, results)
            if isinstance(result, Exception)
        }
        if dead:
            self._rooms[game_id] = [
                (pid, ws) for pid, ws in conns if ws not in dead
            ]

