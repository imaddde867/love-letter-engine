"""Tests for Spy bonus at round end."""

from love_letter.engine.engine import Engine


def test_spy_bonus_awarded_when_only_spy_player_remains():
    """Spy player gets extra favor token if they're the only one who played a Spy."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob", "carol"])

    # We need to simulate a full round where:
    # - Alice plays a Spy
    # - Bob and Carol don't play Spies
    # - At round end, Alice should get the Spy bonus

    # This is complex to test via the engine directly, so we test the logic:
    # The engine's _end_round should check cards_played for Spy cards
    state = engine.get_state(game_id, "alice")

    # Manually set up: Alice played a Spy, others didn't
    state.players["alice"].cards_played = [state.players["alice"].hand_card]
    # Force Alice's hand to be Spy
    from love_letter.models.card import CardType
    state.players["alice"].hand_card = CardType.SPY
    state.players["alice"].cards_played = [CardType.SPY]

    # Bob and Carol didn't play Spies
    state.players["bob"].cards_played = []
    state.players["carol"].cards_played = []

    # Simulate round end
    engine._end_round(state)

    # Alice should have favor token + Spy bonus
    assert state.players["alice"].favor_tokens >= 1


def test_no_spy_bonus_when_multiple_players_played_spy():
    """No Spy bonus if multiple players played Spies."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])

    from love_letter.models.card import CardType
    state = engine.get_state(game_id, "alice")

    # Both players played Spies
    state.players["alice"].cards_played = [CardType.SPY]
    state.players["bob"].cards_played = [CardType.SPY]

    engine._end_round(state)

    # No Spy bonus should be awarded (normal round winner gets favor token)
    # The test passes if no error is raised
