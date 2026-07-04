"""Tests for the Baron card effect."""

from love_letter.engine.effects.baron import BaronEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_baron_lower_value_eliminated():
    """Baron: lower value card is eliminated."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.BARON
    state.players["bob"].hand_card = CardType.GUARD  # Value 1 < Baron value 3

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.BARON,
        player_id="alice",
        other_card=CardType.GUARD,
        target_player="bob",
    )

    BaronEffect.resolve(state, action)
    assert state.players["bob"].is_active is False


def test_baron_higher_value_survives():
    """Baron: higher value card survives."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.BARON
    state.players["bob"].hand_card = CardType.PRINCESS  # Value 9 > Baron value 3

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.BARON,
        player_id="alice",
        other_card=CardType.PRINCESS,
        target_player="bob",
    )

    BaronEffect.resolve(state, action)
    assert state.players["bob"].is_active is True


def test_baron_tie_no_effect():
    """Baron: tied values -> nothing happens."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.BARON
    state.players["bob"].hand_card = CardType.BARON

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.BARON,
        player_id="alice",
        other_card=CardType.BARON,
        target_player="bob",
    )

    BaronEffect.resolve(state, action)
    assert state.players["bob"].is_active is True


def test_baron_requires_target():
    """Baron without target raises ValueError."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.BARON,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    try:
        BaronEffect.resolve(state, action)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "target_player" in str(e).lower()
