"""Unit tests for the domain model: Player and Game."""

import pytest
from unittest.mock import patch

from config import settings
from exceptions import (
    GameAlreadyStartedError,
    GameFullError,
    GameNotInProgressError,
    NotEnoughPlayersError,
    NotHostError,
    NotYourTurnError,
)
from models.game import BOARD, BOARD_SIZE, Game, Player

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_game(n_players: int = 2) -> Game:
    """Return a game with n_players (host = 'Alice')."""
    game = Game("g1", "CODE01", "alice-id", "Alice")
    names = ["Bob", "Charlie", "Dave"]
    for i in range(n_players - 1):
        game.add_player(f"p{i+2}-id", names[i])
    return game


def start_deterministic(game: Game, host_id: str = "alice-id") -> None:
    """Start the game without shuffling so player order is predictable."""
    with patch("models.game.random.shuffle"):
        game.start(host_id)


def roll(game: Game, dice: int) -> None:
    """Roll for the current player with a fixed dice value."""
    current_id = game.players[game.current_player_index].id
    with patch("models.game.random.randint", return_value=dice):
        game.roll_and_play(current_id)


# ═══════════════════════════════════════════════════════════════════════════════
# Player
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlayer:
    def test_initial_money(self):
        p = Player("id", "Alice")
        assert p.money == settings.STARTING_MONEY

    def test_initial_position(self):
        p = Player("id", "Alice")
        assert p.position == 0

    def test_initial_not_bankrupt(self):
        p = Player("id", "Alice")
        assert p.is_bankrupt is False

    def test_is_host_flag(self):
        p = Player("id", "Alice", is_host=True)
        assert p.is_host is True

    def test_to_dict_keys(self):
        p = Player("id", "Alice")
        d = p.to_dict()
        assert set(d) == {"id", "name", "money", "position", "properties", "is_bankrupt", "is_host"}


# ═══════════════════════════════════════════════════════════════════════════════
# Game initialisation
# ═══════════════════════════════════════════════════════════════════════════════

class TestGameInit:
    def test_initial_status(self):
        game = Game("g1", "CODE01", "alice-id", "Alice")
        assert game.status == "waiting"

    def test_host_added_automatically(self):
        game = Game("g1", "CODE01", "alice-id", "Alice")
        assert len(game.players) == 1
        assert game.players[0].is_host is True

    def test_no_winner_initially(self):
        game = Game("g1", "CODE01", "alice-id", "Alice")
        assert game.winner is None

    def test_board_size(self):
        assert BOARD_SIZE == 24


# ═══════════════════════════════════════════════════════════════════════════════
# Lobby — add_player
# ═══════════════════════════════════════════════════════════════════════════════

class TestAddPlayer:
    def test_adds_player_successfully(self):
        game = Game("g1", "CODE01", "alice-id", "Alice")
        game.add_player("bob-id", "Bob")
        assert len(game.players) == 2

    def test_raises_when_full(self):
        game = make_game(n_players=4)
        with pytest.raises(GameFullError):
            game.add_player("extra-id", "Extra")

    def test_raises_when_game_started(self):
        game = make_game(2)
        start_deterministic(game)
        with pytest.raises(GameAlreadyStartedError):
            game.add_player("late-id", "Late")


# ═══════════════════════════════════════════════════════════════════════════════
# Lobby — start
# ═══════════════════════════════════════════════════════════════════════════════

class TestStartGame:
    def test_status_becomes_playing(self):
        game = make_game(2)
        start_deterministic(game)
        assert game.status == "playing"

    def test_raises_when_not_host(self):
        game = make_game(2)
        with pytest.raises(NotHostError):
            game.start("p2-id")  # Bob is not host

    def test_raises_with_one_player(self):
        game = Game("g1", "CODE01", "alice-id", "Alice")
        with pytest.raises(NotEnoughPlayersError):
            game.start("alice-id")

    def test_shuffle_called(self):
        game = make_game(2)
        with patch("models.game.random.shuffle") as mock_shuffle:
            game.start("alice-id")
        mock_shuffle.assert_called_once_with(game.players)

    def test_current_player_is_zero(self):
        game = make_game(2)
        start_deterministic(game)
        assert game.current_player_index == 0


# ═══════════════════════════════════════════════════════════════════════════════
# Gameplay — roll_and_play errors
# ═══════════════════════════════════════════════════════════════════════════════

class TestRollErrors:
    def test_raises_when_game_not_started(self, two_player_game):
        with pytest.raises(GameNotInProgressError):
            two_player_game.roll_and_play("alice-id")

    def test_raises_when_not_your_turn(self, started_game):
        # current is Alice (index 0); Bob should be rejected
        with pytest.raises(NotYourTurnError):
            with patch("models.game.random.randint", return_value=1):
                started_game.roll_and_play("p2-id")


# ═══════════════════════════════════════════════════════════════════════════════
# Gameplay — movement & actions
# ═══════════════════════════════════════════════════════════════════════════════

class TestMovement:
    def test_player_position_updated(self, started_game):
        alice = started_game.players[0]
        roll(started_game, dice=3)
        assert alice.position == 3

    def test_landing_on_empty_square_changes_nothing(self, started_game):
        """Square 2 = Community Chest (empty): no money change."""
        alice = started_game.players[0]
        money_before = alice.money
        roll(started_game, dice=2)  # lands on square 2
        assert alice.money == money_before

    def test_pass_go_earns_salary(self, started_game):
        """Place Alice near end of board; a roll that wraps should pay salary."""
        alice = started_game.players[0]
        alice.position = BOARD_SIZE - 1  # square 23
        money_before = alice.money
        roll(started_game, dice=1)  # wraps to square 0
        assert alice.money == money_before + settings.GO_SALARY

    def test_land_on_go_earns_salary(self, started_game):
        alice = started_game.players[0]
        alice.position = BOARD_SIZE - 2  # square 22
        money_before = alice.money
        roll(started_game, dice=2)  # lands exactly on GO (square 0)
        assert alice.money == money_before + settings.GO_SALARY

    def test_normal_move_does_not_earn_salary(self, started_game):
        alice = started_game.players[0]
        money_before = alice.money
        roll(started_game, dice=4)  # lands on square 4 (Income Tax, empty)
        # Income Tax is empty — no change
        assert alice.money == money_before


# ═══════════════════════════════════════════════════════════════════════════════
# Gameplay — property transactions
# ═══════════════════════════════════════════════════════════════════════════════

class TestPropertyTransactions:
    def test_buy_unowned_property(self, started_game):
        """Landing on an unowned property deducts price and records ownership."""
        alice = started_game.players[0]
        # Square 1 = Mediterranean Ave, price=60
        roll(started_game, dice=1)
        assert alice.money == settings.STARTING_MONEY - 60
        assert 1 in alice.properties
        assert started_game.property_owners[1] == alice.id

    def test_cant_afford_skips_purchase(self, started_game):
        """If the player cannot afford the property, it stays unowned."""
        alice = started_game.players[0]
        alice.money = 10  # less than Mediterranean Ave price (60)
        roll(started_game, dice=1)
        assert 1 not in alice.properties
        assert 1 not in started_game.property_owners

    def test_landing_on_own_property_does_nothing(self, started_game):
        """Owner landing on their own property pays nothing."""
        alice = started_game.players[0]
        roll(started_game, dice=1)  # Alice buys square 1
        money_after_buy = alice.money

        # Advance turn back to Alice: skip Bob's turn, put Alice on sq 1 again
        bob = started_game.players[1]
        bob.position = 0
        roll(started_game, dice=2)  # Bob's turn — lands on empty sq 2

        alice.position = 0  # reset Alice's position
        roll(started_game, dice=1)  # Alice lands on her own property
        assert alice.money == money_after_buy  # no change

    def test_pay_rent_to_owner(self, started_game):
        """Landing on someone else's property transfers rent."""
        alice = started_game.players[0]
        bob = started_game.players[1]

        # Alice buys square 1 (rent=2)
        roll(started_game, dice=1)
        alice_after_buy = alice.money
        bob_before = bob.money

        # Bob lands on square 1
        bob.position = 0
        roll(started_game, dice=1)  # Bob's turn
        assert bob.money == bob_before - 2
        assert alice.money == alice_after_buy + 2

    def test_pay_rent_to_bankrupt_owner_does_nothing(self, started_game):
        """If the owner is bankrupt, landing on their (ex-)property is free."""
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)  # Alice buys sq 1
        alice.is_bankrupt = True   # artificially mark Alice bankrupt

        bob_money_before = bob.money
        bob.position = 0
        roll(started_game, dice=1)  # Bob's turn — owner is bankrupt
        assert bob.money == bob_money_before  # no rent paid


# ═══════════════════════════════════════════════════════════════════════════════
# Gameplay — bankruptcy
# ═══════════════════════════════════════════════════════════════════════════════

class TestBankruptcy:
    def test_bankrupt_player_marked(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)  # Alice buys sq 1 (rent=2)
        bob.money = 1               # Bob can't afford $2 rent

        bob.position = 0
        roll(started_game, dice=1)  # Bob lands on sq 1 → bankrupt
        assert bob.is_bankrupt is True

    def test_bankrupt_player_loses_money(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)
        bob.money = 1
        bob.position = 0
        roll(started_game, dice=1)
        assert bob.money == 0

    def test_creditor_receives_remaining_money(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)  # Alice buys sq 1 for $60
        bob.money = 1
        alice_money_before = alice.money
        bob.position = 0
        roll(started_game, dice=1)
        # Alice gets Bob's $1 (couldn't pay $2 rent)
        assert alice.money == alice_money_before + 1

    def test_creditor_receives_bankrupt_properties(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        # Give Bob a property first
        bob.properties.append(3)
        started_game.property_owners[3] = bob.id

        roll(started_game, dice=1)  # Alice buys sq 1 (rent=2)
        bob.money = 1
        bob.position = 0
        roll(started_game, dice=1)  # Bob → bankrupt

        assert 3 in alice.properties
        assert started_game.property_owners[3] == alice.id


# ═══════════════════════════════════════════════════════════════════════════════
# Gameplay — turn advancement
# ═══════════════════════════════════════════════════════════════════════════════

class TestTurnAdvancement:
    def test_turn_advances_after_roll(self, started_game):
        assert started_game.current_player_index == 0
        roll(started_game, dice=2)  # Alice's turn
        assert started_game.current_player_index == 1

    def test_turn_wraps_to_first_player(self, started_game):
        roll(started_game, dice=2)  # Alice → index 1 (Bob)
        roll(started_game, dice=2)  # Bob → wraps to index 0 (Alice)
        assert started_game.current_player_index == 0

    def test_turn_skips_bankrupt_player(self):
        """With 3 players where player 1 is bankrupt, turn goes 0 → 2."""
        game = make_game(3)
        start_deterministic(game)
        game.players[1].is_bankrupt = True

        assert game.current_player_index == 0
        roll(game, dice=2)  # Alice's turn → should skip bankrupt Bob
        assert game.current_player_index == 2


# ═══════════════════════════════════════════════════════════════════════════════
# Gameplay — win condition
# ═══════════════════════════════════════════════════════════════════════════════

class TestWinCondition:
    def test_last_standing_wins(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)  # Alice buys sq 1 (rent=2)
        bob.money = 1               # Bob cannot pay $2 rent
        bob.position = 0
        roll(started_game, dice=1)  # Bob → bankrupt → Alice wins

        assert started_game.status == "finished"
        assert started_game.winner == "Alice"

    def test_game_finished_blocks_further_rolls(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)
        bob.money = 1
        bob.position = 0
        roll(started_game, dice=1)  # Bob bankrupt → finished

        with pytest.raises(GameNotInProgressError):
            started_game.roll_and_play(alice.id)

    def test_to_dict_contains_winner(self, started_game):
        alice = started_game.players[0]
        bob = started_game.players[1]

        roll(started_game, dice=1)
        bob.money = 1
        bob.position = 0
        roll(started_game, dice=1)

        d = started_game.to_dict()
        assert d["winner"] == "Alice"
        assert d["status"] == "finished"

