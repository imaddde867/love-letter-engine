"""Tests for the Chancellor card effect."""

from love_letter.engine.effects.chancellor import ChancellorEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_chancellor_draws_two_and_returns_two():
    """Chancellor: draw 2 cards, keep 1, return CHANCELLOR + non-kept drawn card."""
    state = GameState(game_id="g1", round=1, deck=[CardType.GUARD, CardType.PRIEST])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.CHANCELLOR

    # Keep GUARD, return PRIEST + CHANCELLOR to bottom
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.CHANCELLOR,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    ChancellorEffect.resolve(state, action)
    # Alice should keep the GUARD
    assert state.players["alice"].hand_card == CardType.GUARD
    # Deck should have 2 cards returned to bottom: PRIEST + CHANCELLOR
    assert len(state.deck) == 2
    assert state.deck[0] == CardType.PRIEST
    assert state.deck[1] == CardType.CHANCELLOR


def test_chancellor_regression_drawn_card_matches_other_card():
    """Regression: CHANCELLOR must not be lost when drawn card matches other_card.

    When the player keeps a drawn card (other_card equals one of the drawn cards),
    both the played CHANCELLOR and the non-matching drawn card must return to the deck.
    Previously only the non-matching drawn card returned, causing deck desync.
    """
    state = GameState(game_id="g1", round=1, deck=[CardType.PRIEST, CardType.BARON])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.CHANCELLOR

    # Keep PRIEST (drawn), return BARON + CHANCELLOR
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.CHANCELLOR,
        player_id="alice",
        other_card=CardType.PRIEST,
    )

    initial_deck = 2
    ChancellorEffect.resolve(state, action)

    # Alice keeps the drawn PRIEST
    assert state.players["alice"].hand_card == CardType.PRIEST
    # Deck integrity: CHANCELLOR + non-kept drawn card returned (2 cards total)
    assert len(state.deck) == initial_deck
    assert CardType.BARON in state.deck
    assert CardType.CHANCELLOR in state.deck


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


def test_chancellor_rejects_kept_card_outside_available_choices():
    """Chancellor cannot keep a card that was not in the choice set."""
    import pytest

    from love_letter.engine.errors import InvalidActionError

    state = GameState(game_id="g1", round=1, deck=[CardType.PRIEST, CardType.BARON])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.GUARD

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.CHANCELLOR,
        player_id="alice",
        other_card=CardType.PRINCESS,
    )

    with pytest.raises(InvalidActionError) as exc_info:
        ChancellorEffect.resolve(state, action)

    assert [v.code for v in exc_info.value.violations] == ["CARD_NOT_AVAILABLE"]
