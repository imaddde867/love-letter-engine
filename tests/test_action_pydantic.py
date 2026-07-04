"""Tests for Pydantic-compatible Action model."""

from love_letter.models.action import Action
from love_letter.models.card import CardType


def test_action_can_be_created_from_dict():
    """Action can be instantiated from a dict (Pydantic BaseModel behavior)."""
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
        target_player="bob",
        guess=CardType.BARON,
    )
    assert action.card_in_hand == CardType.GUARD
    assert action.player_id == "alice"
    assert action.guess == CardType.BARON


def test_action_can_be_created_from_json():
    """Action can be parsed from JSON (FastAPI request body)."""
    import json

    data = {
        "action_type": "play_card",
        "card_in_hand": 1,
        "other_card": 2,
        "player_id": "alice",
        "target_player": "bob",
        "guess": 3,
    }
    action = Action.model_validate(data)
    assert action.card_in_hand == CardType.GUARD
    assert action.other_card == CardType.PRIEST
    assert action.guess == CardType.BARON


def test_action_optional_fields_default_to_none():
    """Optional fields default to None when not provided."""
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        other_card=CardType.PRINCESS,
        player_id="alice",
    )
    assert action.target_player is None
    assert action.guess is None


def test_action_card_type_serialization():
    """CardType serializes to its int value and back."""
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.KING,
        other_card=CardType.COUNTESS,
        player_id="alice",
    )
    data = action.model_dump()
    assert data["card_in_hand"] == 7
    assert data["other_card"] == 8

    restored = Action.model_validate(data)
    assert restored.card_in_hand == CardType.KING
    assert restored.other_card == CardType.COUNTESS
