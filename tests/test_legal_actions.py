"""Tests for the legal action generator."""

from love_letter.engine.engine import Engine
from love_letter.engine.legal_actions import available_actions
from love_letter.models.action import Action
from love_letter.models.card import CardType


def _make_state(hand: CardType, deck_first: CardType | None = None, player_id: str = "alice"):
    """Helper to create a simple 2-player state with known cards."""
    engine = Engine()
    game_id = engine.create_game([player_id, "bob"])
    state = engine.get_state(game_id, player_id)
    state.players[player_id].hand_card = hand
    if deck_first is not None:
        state.deck = [deck_first] + [c for c in state.deck]
    return state


def test_available_actions_returns_list():
    """available_actions returns a list of Actions."""
    state = _make_state(CardType.GUARD)
    result = available_actions(state, "alice")
    assert isinstance(result, list)


def test_available_actions_non_empty_for_guard():
    """Guard actions include at least one valid action."""
    state = _make_state(CardType.GUARD)
    result = available_actions(state, "alice")
    assert len(result) > 0


def test_available_actions_filter_by_player():
    """available_actions only returns actions for the given player."""
    state = _make_state(CardType.GUARD)
    result = available_actions(state, "alice")
    for action in result:
        assert action.player_id == "alice"


def test_available_actions_card_in_hand_matches_turn_cards():
    """Every returned action's card_in_hand is one of the player's two turn cards."""
    state = _make_state(CardType.GUARD, CardType.PRIEST)
    result = available_actions(state, "alice")
    for action in result:
        assert action.card_in_hand in (CardType.GUARD, CardType.PRIEST)


def test_available_actions_other_card_completes_pair():
    """Every returned action's other_card completes the pair with card_in_hand."""
    state = _make_state(CardType.GUARD, CardType.PRIEST)
    result = available_actions(state, "alice")
    for action in result:
        pair = sorted([action.card_in_hand, action.other_card])
        expected = sorted([CardType.GUARD, CardType.PRIEST])
        assert pair == expected


def test_available_actions_guard_requires_guess():
    """Guard actions must include a guess that is not Guard."""
    state = _make_state(CardType.GUARD)
    result = available_actions(state, "alice")
    guard_actions = [a for a in result if a.card_in_hand == CardType.GUARD]
    for action in guard_actions:
        assert action.guess is not None
        assert action.guess != CardType.GUARD
        assert action.target_player is not None


def test_available_actions_targeting_cards_require_target():
    """Priest, Baron, King, Prince require a target_player."""
    state = _make_state(CardType.PRIEST)
    result = available_actions(state, "alice")
    targeting = [a for a in result if a.card_in_hand in (
        CardType.PRIEST, CardType.BARON, CardType.KING, CardType.PRINCE
    )]
    for action in targeting:
        assert action.target_player is not None
        assert action.target_player != "alice"


def test_available_actions_no_target_for_non_targeting():
    """Handmaid, Countess, Princess, Chancellor, Spy do not require target."""
    state = _make_state(CardType.HANDMAID)
    result = available_actions(state, "alice")
    for action in result:
        if action.card_in_hand in (CardType.HANDMAID, CardType.COUNTESS, CardType.PRINCESS,
                                    CardType.CHANCELLOR, CardType.SPY):
            assert action.target_player is None


def test_available_actions_princess_eliminated():
    """Playing Princess eliminates the actor."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.PRINCESS
    state.deck = [CardType.GUARD]

    actions_before = engine.get_state(game_id, "alice")
    princess_action = Action(
        action_type="play_card",
        card_in_hand=CardType.PRINCESS,
        other_card=None,
        player_id="alice",
    )
    state = engine.execute_action(game_id, "alice", princess_action)

    assert not state.players["alice"].is_active


def test_available_actions_excludes_eliminated_targets():
    """Available actions do not include eliminated players as targets."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob", "carol"])
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.PRIEST
    state.deck = [CardType.GUARD]
    state.players["carol"].is_active = False  # Eliminate carol

    result = available_actions(state, "alice")
    targeting = [a for a in result if a.target_player]
    for action in targeting:
        assert action.target_player != "carol"


def test_available_actions_chancellor_sets_other_card_to_none():
    """Chancellor actions have other_card=None per ADR-009 simplification."""
    state = _make_state(CardType.CHANCELLOR)
    result = available_actions(state, "alice")
    chancellor_actions = [a for a in result if a.card_in_hand == CardType.CHANCELLOR]
    for action in chancellor_actions:
        assert action.other_card is None


def test_available_actions_countess_with_king_pair():
    """Countess + King pair generates valid Countess and King actions."""
    state = _make_state(CardType.COUNTESS, CardType.KING)
    result = available_actions(state, "alice")
    card_types = {a.card_in_hand for a in result}
    assert CardType.COUNTESS in card_types
    assert CardType.KING in card_types


def test_available_actions_guard_generates_all_9_guesses():
    """Guard actions include all 9 non-Guard card types as guesses."""
    state = _make_state(CardType.GUARD, CardType.PRIEST)
    result = available_actions(state, "alice")
    guard_actions = [a for a in result if a.card_in_hand == CardType.GUARD]
    guesses = {a.guess for a in guard_actions}
    expected_guesses = {c for c in CardType if c != CardType.GUARD}
    assert guesses == expected_guesses


def test_available_actions_guard_guess_count_matches_targets_times_guesses():
    """Guard generates len(targets) * 9 distinct actions (after dedup)."""
    state = _make_state(CardType.GUARD, CardType.PRIEST)
    result = available_actions(state, "alice")
    guard_actions = [a for a in result if a.card_in_hand == CardType.GUARD]
    targets = {a.target_player for a in guard_actions}
    guesses = {a.guess for a in guard_actions}
    assert len(targets) == 1  # bob is the only valid target
    assert len(guesses) == 9  # all non-Guard card types
    assert len(guard_actions) == 1 * 9
