"""Tests for the Spy card effect."""

from love_letter.engine.effects.spy import SpyEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_spy_no_immediate_effect():
    """Spy has no immediate effect on game state."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.SPY

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.SPY,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    # Should not raise
    result = SpyEffect.resolve(state, action)
    assert result is state


def test_spy_does_not_eliminate_self():
    """Spy playing does not eliminate the player."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.SPY

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.SPY,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    SpyEffect.resolve(state, action)
    assert state.players["alice"].is_active is True
