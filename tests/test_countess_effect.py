"""Tests for the Countess card effect."""

from love_letter.engine.effects.countess import CountessEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_countess_no_immediate_effect():
    """Countess has no immediate effect on game state."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.COUNTESS

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.COUNTESS,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    # Should not raise
    result = CountessEffect.resolve(state, action)
    assert result is state


def test_countess_does_not_eliminate_self():
    """Countess playing does not eliminate the player."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.COUNTESS

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.COUNTESS,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    CountessEffect.resolve(state, action)
    assert state.players["alice"].is_active is True
