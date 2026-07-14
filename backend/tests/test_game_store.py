"""Unit tests for GameStore (repository layer)."""

import pytest

from exceptions import GameNotFoundError
from services.game_store import GameStore


@pytest.fixture
def store() -> GameStore:
    return GameStore()


class TestCreateGame:
    def test_returns_game_instance(self, store):
        game = store.create_game("host-id", "Alice")
        assert game.game_id is not None
        assert game.join_code is not None

    def test_join_code_length(self, store):
        game = store.create_game("host-id", "Alice")
        assert len(game.join_code) == 6

    def test_join_code_uppercase(self, store):
        game = store.create_game("host-id", "Alice")
        assert game.join_code == game.join_code.upper()

    def test_host_added_as_player(self, store):
        game = store.create_game("host-id", "Alice")
        assert game.players[0].id == "host-id"
        assert game.players[0].is_host is True

    def test_unique_codes(self, store):
        """All generated join codes must be unique."""
        codes = {store.create_game(f"host-{i}", f"P{i}").join_code for i in range(20)}
        assert len(codes) == 20  # no collisions


class TestGetGame:
    def test_get_existing_game(self, store):
        game = store.create_game("host-id", "Alice")
        fetched = store.get(game.game_id)
        assert fetched is game

    def test_get_missing_game_raises(self, store):
        with pytest.raises(GameNotFoundError):
            store.get("non-existent-id")

    def test_get_returns_same_object(self, store):
        """Mutations on the returned object should persist (same reference)."""
        game = store.create_game("host-id", "Alice")
        store.get(game.game_id).last_action = "mutated"
        assert store.get(game.game_id).last_action == "mutated"


class TestGetByCode:
    def test_get_by_exact_code(self, store):
        game = store.create_game("host-id", "Alice")
        fetched = store.get_by_code(game.join_code)
        assert fetched is game

    def test_get_by_code_case_insensitive(self, store):
        game = store.create_game("host-id", "Alice")
        lower_code = game.join_code.lower()
        fetched = store.get_by_code(lower_code)
        assert fetched is game

    def test_get_by_wrong_code_raises(self, store):
        with pytest.raises(GameNotFoundError):
            store.get_by_code("XXXXXX")

