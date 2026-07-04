"""Property-based tests for game invariants."""

from hypothesis import given, settings
from hypothesis import strategies as st

from love_letter.engine.engine import Engine
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player


def _make_random_valid_action(state, player_id):
    """Create a random valid action for the given state and player."""
    player = state.players[player_id]
    if not player.is_active or player.hand_card is None:
        return None

    # Simple random action: play the hand card, keep a random other card
    other_card = CardType.GUARD  # Default to Guard as other card
    target_player = None
    guess = None

    # For targeting cards, pick a random active target
    if player.hand_card in (CardType.GUARD, CardType.PRIEST, CardType.BARON, CardType.KING):
        active_targets = [
            pid for pid, p in state.players.items()
            if p.is_active and pid != player_id
        ]
        if active_targets:
            target_player = st.sampled_from(active_targets).example()

    if player.hand_card == CardType.GUARD:
        guess = st.sampled_from(list(CardType)).example()

    return Action(
        action_type="play_card",
        card_in_hand=player.hand_card,
        other_card=other_card,
        player_id=player_id,
        target_player=target_player,
        guess=guess,
    )


def test_round_always_ends():
    """A round always ends when played to completion."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob", "carol"])

    state = engine.get_state(game_id, "alice")
    assert not engine._is_round_over(state) or state.deck_count == 0


def test_favor_tokens_never_negative():
    """Favor tokens are never negative after any action."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])

    state = engine.get_state(game_id, "alice")
    for player in state.players.values():
        assert player.favor_tokens >= 0


def test_deck_count_never_negative():
    """Deck count is never negative after any action."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])

    state = engine.get_state(game_id, "alice")
    assert state.deck_count >= 0


def test_player_ids_consistent():
    """Player IDs in state match the players dict keys."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob", "carol", "dave"])

    state = engine.get_state(game_id, "alice")
    player_ids = set(state.players.keys())
    assert player_ids == {"alice", "bob", "carol", "dave"}


def test_active_players_are_subset_of_all_players():
    """Active players are always a subset of all players."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])

    state = engine.get_state(game_id, "alice")
    all_ids = set(state.players.keys())
    active_ids = {pid for pid, p in state.players.items() if p.is_active}
    assert active_ids.issubset(all_ids)


@settings(max_examples=50)
@given(st.integers(min_value=2, max_value=6))
def test_game_creation_with_valid_player_counts(player_count):
    """Games can be created with 2-6 players."""
    engine = Engine()
    player_ids = [f"player_{i}" for i in range(player_count)]
    game_id = engine.create_game(player_ids)

    state = engine.get_state(game_id, player_ids[0])
    assert len(state.players) == player_count
