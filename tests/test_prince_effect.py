"""Tests for the Prince card effect."""

from love_letter.engine.effects.prince import PrinceEffect
from love_letter.engine.engine import Engine
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


def test_prince_without_target_is_a_no_op():
    """Prince with no target_player (no valid targets) has no effect."""
    state = GameState(game_id="g1", round=1)
    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCE,
        player_id="alice",
        other_card=CardType.BARON,
    )

    result = PrinceEffect.resolve(state, action)
    assert result is state


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


def _total_card_count(state) -> int:
    """Count every card still tracked by the state: deck, hands, facedown,
    and the public played/discard pile."""
    in_hands = sum(1 for p in state.players.values() if p.hand_card is not None)
    in_facedown = 1 if state.facedown_card is not None else 0
    return len(state.deck) + in_hands + in_facedown + len(state.played_cards)


def test_prince_discard_is_not_lost_when_round_rebuilds_deck():
    """Regression: a Prince-forced discard must survive into the next round.

    Previously the target's discarded card was set to hand_card=None and
    never recorded anywhere, so _start_new_round's deck rebuild (which
    sums state.deck + played_cards + facedown_card + remaining hands)
    silently dropped it — the game lost a card every time Prince forced
    a non-Princess discard.
    """
    state = GameState(game_id="g1", round=1, deck=[CardType.GUARD])
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["alice"].hand_card = CardType.PRINCE
    state.players["bob"].hand_card = CardType.BARON

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCE,
        player_id="alice",
        other_card=CardType.HANDMAID,
        target_player="bob",
    )
    PrinceEffect.resolve(state, action)
    assert state.players["bob"].hand_card == CardType.GUARD  # redrawn

    # Mimic execute_action's own bookkeeping for alice's turn: the engine
    # (not the effect) records the played card and updates her hand.
    state.played_cards.append(
        {"player_id": "alice", "card": CardType.PRINCE, "target_player": "bob"}
    )
    state.players["alice"].hand_card = CardType.HANDMAID

    # Tracked right now: alice=Handmaid, bob=Guard, played_cards=[Prince, Baron].
    total_before = _total_card_count(state)
    assert total_before == 4

    # Force the round to end and rebuild the deck for round 2.
    state.deck = []
    state.facedown_card = None
    Engine()._start_new_round(state)

    assert _total_card_count(state) == total_before
