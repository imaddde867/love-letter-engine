"""Tests for the King card effect."""

from love_letter.engine.effects.king import KingEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_king_swaps_hands():
    """King: swap hands with target."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.KING
    state.players["alice"].hand_card = CardType.GUARD
    state.players["bob"].hand_card = CardType.PRINCESS

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.KING,
        player_id="alice",
        other_card=CardType.PRINCESS,
        target_player="bob",
    )

    KingEffect.resolve(state, action)
    # Hands should be swapped
    assert state.players["alice"].hand_card == CardType.PRINCESS
    assert state.players["bob"].hand_card == CardType.GUARD


def test_king_without_target_is_a_no_op():
    """King with no target_player (no valid targets) has no effect."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.KING,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    result = KingEffect.resolve(state, action)
    assert result is state
