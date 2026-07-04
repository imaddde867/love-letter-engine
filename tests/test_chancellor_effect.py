"""Tests for the Chancellor card effect."""

from love_letter.engine.effects.chancellor import ChancellorEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_chancellor_draws_two_keeps_one_and_returns_two_to_bottom():
    """Chancellor chooses from the kept card plus two drawn cards."""
    state = GameState(game_id="g1", round=1, deck=[CardType.GUARD, CardType.PRIEST])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.KING

    # Keep drawn PRIEST, return original KING then drawn GUARD to bottom.
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.CHANCELLOR,
        player_id="alice",
        other_card=CardType.KING,
        chancellor_keep_card=CardType.PRIEST,
        chancellor_return_order=[CardType.KING, CardType.GUARD],
    )

    ChancellorEffect.resolve(state, action)
    assert state.players["alice"].hand_card == CardType.PRIEST
    assert state.deck == [CardType.KING, CardType.GUARD]


def test_chancellor_empty_deck_no_effect():
    """Chancellor: if deck is empty, no effect."""
    state = GameState(game_id="g1", round=1, deck=[])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.CHANCELLOR

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.CHANCELLOR,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    # Should not raise
    ChancellorEffect.resolve(state, action)
    assert state.players["alice"].hand_card == CardType.GUARD
