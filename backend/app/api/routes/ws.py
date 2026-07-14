"""WebSocket endpoint — real-time game communication."""

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from dependencies import get_manager, get_store
from exceptions import (
    GameNotFoundError,
    MonopolyError,
    PlayerNotFoundError,
)
from app.services.connection_manager import ConnectionManager
from app.services.game_store import GameStore

router = APIRouter(tags=["websocket"])


@router.websocket("/api/games/{game_id}/ws")
async def game_websocket(
    websocket: WebSocket,
    game_id: str,
    player_id: str = Query(...),
    store: GameStore = Depends(get_store),
    manager: ConnectionManager = Depends(get_manager),
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

            if msg_type == "start_game":
                await _handle_start(websocket, game, player_id, manager)

            elif msg_type == "roll_dice":
                await _handle_roll(websocket, game, player_id, manager)

            # Unknown message types are silently ignored (forward-compat).

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
        # If the game is in progress, mark the disconnected player as bankrupt
        # and check if only one player remains.
        if game.status == "playing":
            player_obj = game.get_player(player_id)
            if player_obj and not player_obj.is_bankrupt:
                player_obj.is_bankrupt = True
                player_obj.has_quit = True
                game.last_action = f"{player_obj.name} logout."
                game.check_last_player_wins()
            await manager.broadcast_state(game_id, game.to_dict())


# ── Handlers ──────────────────────────────────────────────────────────────────

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

