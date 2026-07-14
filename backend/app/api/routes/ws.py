"""WebSocket endpoint — real-time game communication."""

from typing import Annotated

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from dependencies import ManagerDep, StoreDep
from exceptions import (
    GameNotFoundError,
    MonopolyError,
)
from app.services.connection_manager import ConnectionManager

router = APIRouter(tags=["websocket"])


@router.websocket("/api/games/{game_id}/ws")
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    player_id: Annotated[str, Query(...)],
    store: StoreDep,
    manager: ManagerDep,
) -> None:
    # ── Validate before accepting ──────────────────────────────────────────────
    try:
        game = store.get(game_id)
    except GameNotFoundError:
        await websocket.accept()
        await manager.send_error(websocket, "Game not found")
        await websocket.close(code=1008)
        return

    player = game.get_player(player_id)
    if player is None:
        await websocket.accept()
        await manager.send_error(websocket, "Player not found in this game")
        await websocket.close(code=1008)
        return

    # ── Handshake ──────────────────────────────────────────────────────────────
    await websocket.accept()
    manager.connect(game_id, player_id, websocket)

    # Push current state immediately so the client renders without waiting
    await websocket.send_json({"type": "game_state", "state": game.to_dict()})

    # ── Message loop ───────────────────────────────────────────────────────────
    try:
        while True:
            try:
                data: dict = await websocket.receive_json()
            except ValueError:
                await manager.send_error(websocket, "Invalid JSON payload")
                continue

            msg_type: str = data.get("type", "")

            dispatch = {
                "start_game": _handle_start,
                "roll_dice":  _handle_roll,
                "leave_game": _handle_leave,
            }

            if handler := dispatch.get(msg_type):
                await handler(websocket, game, player_id, manager)
                if msg_type == "leave_game":
                    break

            # Unknown message types are silently ignored (forward-compat).

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)


# ── Handlers ──────────────────────────────────────────────────────────────────

async def _handle_leave(
    ws: WebSocket,
    game,
    player_id: str,
    manager: ConnectionManager,
) -> None:
    manager.disconnect(game.game_id, ws)
    if game.status == "playing":
        player_obj = game.get_player(player_id)
        if player_obj and not player_obj.is_bankrupt:
            player_obj.is_bankrupt = True
            player_obj.has_quit = True
            game.last_action = f"{player_obj.name} logged out."
            game.check_last_player_wins()
        await manager.broadcast_state(game.game_id, game.to_dict())


async def _handle_start(
    ws: WebSocket,
    game,
    player_id: str,
    manager: ConnectionManager,
) -> None:
    try:
        game.start(player_id)
        await manager.broadcast_state(game.game_id, game.to_dict())
    except MonopolyError as exc:
        await manager.send_error(ws, str(exc))


async def _handle_roll(
    ws: WebSocket,
    game,
    player_id: str,
    manager: ConnectionManager,
) -> None:
    try:
        game.roll_and_play(player_id)
        await manager.broadcast_state(game.game_id, game.to_dict())
    except MonopolyError as exc:
        await manager.send_error(ws, str(exc))
