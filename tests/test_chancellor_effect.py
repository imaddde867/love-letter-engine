"""Tests for the Chancellor card effect."""

from love_letter.engine.effects.chancellor import ChancellorEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_chancellor_draws_two_and_returns_two():
    """Chancellor: draw 2 cards, keep 1, return 2 to bottom of deck."""
    state = GameState(game_id="g1", round=1, deck=[CardType.GUARD, CardType.PRIEST])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.CHANCELLOR

    # Keep GUARD, return PRIEST and the other drawn card to bottom
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.CHANCELLOR,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    ChancellorEffect.resolve(state, action)
    # Alice should keep the GUARD
    assert state.players["alice"].hand_card == CardType.GUARD
    # Deck should have 2 cards returned to bottom
    assert len(state.deck) == 2


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
