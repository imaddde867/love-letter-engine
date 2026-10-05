"""Tests for the Priest card effect."""

from love_letter.engine.effects.priest import PriestEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_priest_without_target_is_a_no_op():
    """Priest with no target_player (no valid targets) has no effect."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRIEST,
        player_id="alice",
        other_card=CardType.BARON,
    )

    result = PriestEffect.resolve(state, action)
    assert result is state


def test_priest_does_not_change_state():
    """Priest reveals information but does not change game state."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.PRIEST
    state.players["bob"].hand_card = CardType.BARON

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRIEST,
        player_id="alice",
        other_card=CardType.BARON,
        target_player="bob",
    )

    # Should not raise
    result = PriestEffect.resolve(state, action)
    assert result is state
    assert state.players["bob"].is_active is True
