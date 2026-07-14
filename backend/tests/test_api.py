"""Integration tests for REST endpoints and WebSocket routes.

FastAPI's TestClient drives the full ASGI stack (middleware, DI, lifespan)
synchronously, including WebSocket connections via client.websocket_connect().
"""

import pytest
from unittest.mock import patch


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def create_game(client, name: str = "Alice") -> dict:
    resp = client.post("/api/games", json={"player_name": name})
    assert resp.status_code == 201
    return resp.json()


def join_game(client, code: str, name: str) -> dict:
    resp = client.post(f"/api/games/join?code={code}", json={"player_name": name})
    assert resp.status_code == 200
    return resp.json()


def ws_start(client, game_id: str, player_id: str) -> dict:
    """Open a WebSocket, send start_game, return the resulting game state."""
    with client.websocket_connect(
        f"/api/games/{game_id}/ws?player_id={player_id}"
    ) as ws:
        ws.receive_json()                        # discard initial state
        with patch("models.game.random.shuffle"):
            ws.send_json({"type": "start_game"})
            return ws.receive_json()["state"]


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/games
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateGameEndpoint:
    def test_returns_201(self, client):
        resp = client.post("/api/games", json={"player_name": "Alice"})
        assert resp.status_code == 201

    def test_response_shape(self, client):
        data = create_game(client)
        assert {"game_id", "join_code", "player_id", "player_name"} <= data.keys()

    def test_join_code_is_6_chars(self, client):
        data = create_game(client)
        assert len(data["join_code"]) == 6

    def test_empty_name_returns_422(self, client):
        resp = client.post("/api/games", json={"player_name": ""})
        assert resp.status_code == 422

    def test_missing_name_returns_422(self, client):
        resp = client.post("/api/games", json={})
        assert resp.status_code == 422

    def test_name_too_long_returns_422(self, client):
        resp = client.post("/api/games", json={"player_name": "A" * 21})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/games/join
# ═══════════════════════════════════════════════════════════════════════════════

class TestJoinGameEndpoint:
    def test_join_success(self, client):
        alice = create_game(client, "Alice")
        bob = join_game(client, alice["join_code"], "Bob")
        assert bob["game_id"] == alice["game_id"]
        assert bob["player_id"] != alice["player_id"]

    def test_join_wrong_code_returns_404(self, client):
        resp = client.post("/api/games/join?code=ZZZZZZ", json={"player_name": "Bob"})
        assert resp.status_code == 404

    def test_join_full_game_returns_409(self, client):
        alice = create_game(client, "Alice")
        code = alice["join_code"]
        for name in ["Bob", "Charlie", "Dave"]:
            join_game(client, code, name)
        resp = client.post(f"/api/games/join?code={code}", json={"player_name": "Extra"})
        assert resp.status_code == 409

    def test_join_started_game_returns_409(self, client):
        alice = create_game(client)
        join_game(client, alice["join_code"], "Bob")
        ws_start(client, alice["game_id"], alice["player_id"])

        resp = client.post(
            f"/api/games/join?code={alice['join_code']}",
            json={"player_name": "Late"},
        )
        assert resp.status_code == 409

    def test_join_code_case_insensitive(self, client):
        alice = create_game(client)
        lower = alice["join_code"].lower()
        resp = client.post(f"/api/games/join?code={lower}", json={"player_name": "Bob"})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/games/{game_id}
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetGameEndpoint:
    def test_returns_200(self, client):
        alice = create_game(client)
        resp = client.get(f"/api/games/{alice['game_id']}")
        assert resp.status_code == 200

    def test_state_shape(self, client):
        alice = create_game(client)
        state = client.get(f"/api/games/{alice['game_id']}").json()
        expected_keys = {"game_id", "join_code", "status", "players",
                         "board", "last_action", "winner"}
        assert expected_keys <= state.keys()

    def test_initial_status_is_waiting(self, client):
        alice = create_game(client)
        state = client.get(f"/api/games/{alice['game_id']}").json()
        assert state["status"] == "waiting"

    def test_unknown_id_returns_404(self, client):
        resp = client.get("/api/games/does-not-exist")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket
# ═══════════════════════════════════════════════════════════════════════════════

class TestWebSocket:
    def test_connect_receives_initial_state(self, client):
        alice = create_game(client)
        with client.websocket_connect(
            f"/api/games/{alice['game_id']}/ws?player_id={alice['player_id']}"
        ) as ws:
            msg = ws.receive_json()
        assert msg["type"] == "game_state"
        assert msg["state"]["status"] == "waiting"

    def test_invalid_game_id_closes_connection(self, client):
        from starlette.websockets import WebSocketDisconnect
        with client.websocket_connect("/api/games/bad-id/ws?player_id=any") as ws:
            # Server sends an error message before closing
            msg = ws.receive_json()
            assert msg["type"] == "error"
            # Next receive should raise (connection closed by server)
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()

    def test_invalid_player_id_closes_connection(self, client):
        from starlette.websockets import WebSocketDisconnect
        alice = create_game(client)
        with client.websocket_connect(
            f"/api/games/{alice['game_id']}/ws?player_id=wrong-id"
        ) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "error"
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()

    def test_start_game_changes_status(self, client):
        alice = create_game(client)
        join_game(client, alice["join_code"], "Bob")
        state = ws_start(client, alice["game_id"], alice["player_id"])
        assert state["status"] == "playing"

    def test_non_host_cannot_start(self, client):
        alice = create_game(client)
        bob = join_game(client, alice["join_code"], "Bob")

        with client.websocket_connect(
            f"/api/games/{alice['game_id']}/ws?player_id={bob['player_id']}"
        ) as ws:
            ws.receive_json()                        # initial state
            ws.send_json({"type": "start_game"})
            response = ws.receive_json()

        assert response["type"] == "error"

    def test_roll_dice_advances_game(self, client):
        alice = create_game(client)
        join_game(client, alice["join_code"], "Bob")
        state = ws_start(client, alice["game_id"], alice["player_id"])

        # Find current player
        current = state["players"][state["current_player_index"]]

        with client.websocket_connect(
            f"/api/games/{state['game_id']}/ws?player_id={current['id']}"
        ) as ws:
            ws.receive_json()                        # initial state
            ws.send_json({"type": "roll_dice"})
            new_state = ws.receive_json()["state"]

        # After roll, it's someone else's turn (or game is finished)
        player_after = new_state["players"][new_state["current_player_index"]]
        last_action = new_state["last_action"]
        assert current["name"] in last_action      # action mentions the player

    def test_wrong_turn_returns_error(self, client):
        alice = create_game(client)
        bob = join_game(client, alice["join_code"], "Bob")
        state = ws_start(client, alice["game_id"], alice["player_id"])

        # Find who is NOT the current player
        current_idx = state["current_player_index"]
        wrong_player = state["players"][1 - current_idx]

        with client.websocket_connect(
            f"/api/games/{state['game_id']}/ws?player_id={wrong_player['id']}"
        ) as ws:
            ws.receive_json()
            ws.send_json({"type": "roll_dice"})
            response = ws.receive_json()

        assert response["type"] == "error"

    def test_invalid_json_returns_error(self, client):
        alice = create_game(client)
        with client.websocket_connect(
            f"/api/games/{alice['game_id']}/ws?player_id={alice['player_id']}"
        ) as ws:
            ws.receive_json()
            ws.send_text("not json at all {{")
            response = ws.receive_json()
        assert response["type"] == "error"

