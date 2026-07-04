"""Tests for the Engine core."""

import pytest


def test_create_game_returns_id():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    assert isinstance(game_id, str)
    assert len(game_id) > 0


def test_create_game_adds_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert "alice" in state.players
    assert "bob" in state.players


def test_create_game_sets_round_to_one():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert state.round == 1


def test_create_game_sets_favor_threshold_for_two_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    # 2 players -> threshold is 6
    assert state.favor_token_threshold == 6


def test_create_game_for_four_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["a", "b", "c", "d"])
    state = engine.get_state(game_id, "a")
    # 4 players -> threshold is 4
    assert state.favor_token_threshold == 4


def test_get_state_returns_state_for_player():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert state.game_id == game_id
    assert "alice" in state.players


def test_get_state_for_nonexistent_game_raises():
    from love_letter.engine.engine import Engine

    engine = Engine()
    with pytest.raises(KeyError):
        engine.get_state("nonexistent", "alice")


def test_get_state_for_invalid_player_raises():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    with pytest.raises(KeyError):
        engine.get_state(game_id, "charlie")


def test_create_multiple_games():
    from love_letter.engine.engine import Engine

    engine = Engine()
    g1 = engine.create_game(["alice", "bob"])
    g2 = engine.create_game(["carol", "dave"])
    assert g1 != g2


def test_get_state_two_player_has_two_players():
    from love_letter.engine.engine import Engine

    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    assert len(state.players) == 2
