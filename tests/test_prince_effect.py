"""Tests for the Prince card effect."""

from love_letter.engine.effects.prince import PrinceEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


def test_prince_target_discards_and_redraws():
    """Prince: target discards hand and draws new card."""
    state = GameState(game_id="g1", round=1, deck=[CardType.GUARD])
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.PRINCE
    state.players["bob"].hand_card = CardType.BARON

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCE,
        player_id="alice",
        other_card=CardType.BARON,
        target_player="bob",
    )

    PrinceEffect.resolve(state, action)
    # Bob's hand should be replaced with the drawn card
    assert state.players["bob"].hand_card == CardType.GUARD
    assert len(state.deck) == 0


def test_prince_princess_discard_eliminate():
    """Prince: if target discards Princess, they are eliminated."""
    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.PRINCE
    state.players["bob"].hand_card = CardType.PRINCESS

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCE,
        player_id="alice",
        other_card=CardType.BARON,
        target_player="bob",
    )

    PrinceEffect.resolve(state, action)
    assert state.players["bob"].is_active is False


def test_prince_requires_target():
    """Prince without target raises ValueError."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCE,
        player_id="alice",
        other_card=CardType.BARON,
    )

    try:
        PrinceEffect.resolve(state, action)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "target_player" in str(e).lower()


def test_prince_self_target():
    """Prince can target yourself."""
    state = GameState(game_id="g1", round=1, deck=[CardType.GUARD])
    state.players["alice"] = Player(id="alice")
    state.players["alice"].hand_card = CardType.PRINCE

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCE,
        player_id="alice",
        other_card=CardType.BARON,
        target_player="alice",
    )

    PrinceEffect.resolve(state, action)
    # Alice should have drawn a new card
    assert state.players["alice"].hand_card == CardType.GUARD
