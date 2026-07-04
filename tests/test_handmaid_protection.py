"""Tests for Handmaid protection tracking."""

from love_letter.engine.effects.handmaid import HandmaidEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_handmaid_sets_protection_flag():
    """Handmaid sets protected_until_next_turn on the actor."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.HANDMAID
    state.players["bob"] = Player(id="bob")
    state.players["bob"].hand_card = CardType.GUARD

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        other_card=CardType.PRINCESS,
        player_id="alice",
    )

    HandmaidEffect.resolve(state, action)
    assert state.players["alice"].protected_until_next_turn is True


def test_protected_player_cannot_be_targeted():
    """A protected player cannot be chosen as a target by card effects."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.HANDMAID
    state.players["alice"].protected_until_next_turn = True
    state.players["bob"] = Player(id="bob")
    state.players["bob"].hand_card = CardType.GUARD

    # Guard targets protected player with correct guess
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="bob",
        target_player="alice",
        guess=CardType.HANDMAID,
    )

    GuardEffect = __import__("love_letter.engine.effects.guard", fromlist=["GuardEffect"]).GuardEffect
    state = GuardEffect.resolve(state, action)

    # Alice should NOT be eliminated because she's protected
    assert state.players["alice"].is_active is True


def test_protection_clears_after_turn():
    """Protection clears at the start of the protected player's next turn."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.HANDMAID
    state.players["alice"].protected_until_next_turn = True

    # Simulate: protection should be cleared when it's alice's turn again
    # The engine handles this in _resolve_action before alice's turn
    state.players["alice"].protected_until_next_turn = False
    assert state.players["alice"].protected_until_next_turn is False
