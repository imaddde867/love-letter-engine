"""Tests for the Engine core."""

import pytest


def test_create_game_returns_id():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    assert isinstance(game_id, str)
    assert len(game_id) > 0


def test_create_game_adds_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert "alice" in state.players
    assert "bob" in state.players


def test_create_game_sets_round_to_one():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert state.round == 1


def test_create_game_sets_favor_threshold_for_two_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    # 2 players -> threshold is 6
    assert state.favor_token_threshold == 6


def test_create_game_for_four_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["a", "b", "c", "d"])
    state = engine.get_state(game_id, "a")
    # 4 players -> threshold is 4
    assert state.favor_token_threshold == 4


def test_get_state_returns_state_for_player():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert state.game_id == game_id
    assert "alice" in state.players


def test_get_state_for_nonexistent_game_raises():
    from love_letter.engine.engine import Engine

    engine = Engine()
    with pytest.raises(KeyError):
        engine.get_state("nonexistent", "alice")


def test_get_state_for_invalid_player_raises():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    with pytest.raises(KeyError):
        engine.get_state(game_id, "charlie")


def test_create_multiple_games():
    from love_letter.engine.engine import Engine

    engine = Engine()
    g1 = engine.create_game(["alice", "bob"])
    g2 = engine.create_game(["carol", "dave"])
    assert g1 != g2


def test_get_state_two_player_has_two_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert len(state.players) == 2


def test_execute_action_raises_game_over_when_threshold_reached():
    """Engine raises GameOverError when game is over."""
    from love_letter.engine.engine import Engine
    from love_letter.engine.errors import GameOverError
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")

    # Force a player to reach threshold
    for _ in range(10):
        state.players["alice"].add_favor()

    # Create a dummy action for the test
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
        target_player="bob",
        guess=CardType.BARON,
    )

    with pytest.raises(GameOverError):
        engine.execute_action(game_id, "alice", action)


def test_execute_action_rejects_player_out_of_turn_without_mutating_state():
    from love_letter.engine.engine import Engine
    from love_letter.engine.errors import InvalidActionError
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.GUARD
    state.players["bob"].hand_card = CardType.PRIEST
    state.deck = [CardType.BARON]
    state.played_cards = []

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRIEST,
        other_card=CardType.BARON,
        player_id="bob",
        target_player="alice",
    )

    with pytest.raises(InvalidActionError):
        engine.execute_action(game_id, "bob", action)

    assert state.players["bob"].hand_card == CardType.PRIEST
    assert state.deck == [CardType.BARON]
    assert state.played_cards == []


def test_execute_action_rejects_missing_target_without_mutating_state():
    from love_letter.engine.engine import Engine
    from love_letter.engine.errors import InvalidActionError
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.GUARD
    state.players["bob"].hand_card = CardType.PRINCESS
    state.deck = [CardType.PRIEST]
    state.played_cards = []

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
        guess=CardType.PRINCESS,
    )

    with pytest.raises(InvalidActionError):
        engine.execute_action(game_id, "alice", action)

    assert state.players["alice"].hand_card == CardType.GUARD
    assert state.deck == [CardType.PRIEST]
    assert state.played_cards == []


def test_execute_action_rejects_cards_not_available_without_mutating_state():
    from love_letter.engine.engine import Engine
    from love_letter.engine.errors import InvalidActionError
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.GUARD
    state.deck = [CardType.PRIEST]
    state.played_cards = []

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCESS,
        other_card=CardType.PRIEST,
        player_id="alice",
    )

    with pytest.raises(InvalidActionError):
        engine.execute_action(game_id, "alice", action)

    assert state.players["alice"].hand_card == CardType.GUARD
    assert state.deck == [CardType.PRIEST]
    assert state.played_cards == []


def test_create_two_player_game_sets_aside_three_faceup_cards():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")

    assert len(state.faceup_set_aside_cards) == 3
    assert len(state.deck) == 15
