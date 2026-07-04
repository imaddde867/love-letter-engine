"""Tests for the Guard card effect."""

from love_letter.engine.effects.guard import GuardEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_guard_correct_guess_eliminate_target():
    """Guard guesses correctly -> target is eliminated."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.GUARD
    state.players["bob"].hand_card = CardType.BARON

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.PRIEST,
        target_player="bob",
        guess=CardType.BARON,
    )

    GuardEffect.resolve(state, action)
    assert state.players["bob"].is_active is False


def test_guard_wrong_guess_no_effect():
    """Guard guesses incorrectly -> target stays active."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.GUARD
    state.players["bob"].hand_card = CardType.PRIEST

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.PRIEST,
        target_player="bob",
        guess=CardType.BARON,
    )

    GuardEffect.resolve(state, action)
    assert state.players["bob"].is_active is True


def test_guard_requires_target_and_guess():
    """Guard without target or guess raises ValueError."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.PRIEST,
    )

    try:
        GuardEffect.resolve(state, action)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "target_player" in str(e).lower() or "guess" in str(e).lower()


def test_guard_does_not_affect_other_players():
    """Guard only eliminates the targeted player."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["carol"] = Player(id="carol")
    state.players["alice"].hand_card = CardType.GUARD
    state.players["bob"].hand_card = CardType.BARON
    state.players["carol"].hand_card = CardType.PRIEST

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.PRIEST,
        target_player="bob",
        guess=CardType.BARON,
    )

    GuardEffect.resolve(state, action)
    assert state.players["bob"].is_active is False
    assert state.players["carol"].is_active is True
