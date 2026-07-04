"""Tests for the Princess card effect."""

from love_letter.engine.effects.princess import PrincessEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_princess_discard_eliminate():
    """Princess: discard = elimination."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.PRINCESS

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCESS,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    PrincessEffect.resolve(state, action)
    assert state.players["alice"].is_active is False


def test_princess_does_not_affect_others():
    """Princess only eliminates the player who played it."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.PRINCESS
    state.players["bob"].hand_card = CardType.GUARD

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCESS,
        player_id="alice",
        other_card=CardType.GUARD,
    )

    PrincessEffect.resolve(state, action)
    assert state.players["alice"].is_active is False
    assert state.players["bob"].is_active is True
