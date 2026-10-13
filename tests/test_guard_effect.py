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


def test_guard_without_target_is_a_no_op():
    """Guard with no target_player (no valid targets) has no effect."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.PRIEST,
    )

    result = GuardEffect.resolve(state, action)
    assert result is state


def test_guard_requires_guess_when_target_given():
    """Guard with a target but no guess raises ValueError."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob", hand_card=CardType.PRIEST)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.PRIEST,
        target_player="bob",
    )

    try:
        GuardEffect.resolve(state, action)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "guess" in str(e).lower()


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
