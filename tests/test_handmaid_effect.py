"""Tests for the Handmaid card effect."""

from love_letter.engine.effects.handmaid import HandmaidEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_handmaid_no_immediate_effect():
    """Handmaid has no immediate effect on game state."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.HANDMAID

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    # Should not raise
    result = HandmaidEffect.resolve(state, action)
    assert result is state


def test_handmaid_does_not_eliminate_self():
    """Handmaid playing does not eliminate the player."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.HANDMAID

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    HandmaidEffect.resolve(state, action)
    assert state.players["alice"].is_active is True
