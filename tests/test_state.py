"""Tests for the GameState model."""


def test_create_game_state_with_id_and_round():
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    assert state.game_id == "g1"
    assert state.round == 1


def test_game_state_defaults_deck_to_empty():
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    assert state.deck == []


def test_game_state_defaults_players_to_empty():
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    assert state.players == {}


def test_game_state_defaults_current_player_index_zero():
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    assert state.current_player_index == 0


def test_game_state_defaults_played_cards_empty():
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    assert state.played_cards == []


def test_game_state_add_player():
    from love_letter.models.player import Player
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    player = Player(id="alice")
    state.players["alice"] = player
    assert "alice" in state.players
    assert state.players["alice"].id == "alice"


def test_game_state_deck_count():
    from love_letter.models.card import CardType
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    state.deck = [CardType.GUARD, CardType.PRIEST]
    assert state.deck_count == 2


def test_game_state_favor_threshold_for_four_players():
    from love_letter.models.state import GameState

    # 4 players -> threshold is 4
    state = GameState(game_id="g1", round=1, favor_token_threshold=4)
    assert state.favor_token_threshold == 4


def test_game_state_has_active_players():
    from love_letter.models.player import Player
    from love_letter.models.state import GameState

    state = GameState(game_id="g1", round=1)
    state.players["alice"] = Player(id="alice")
    state.players["bob"] = Player(id="bob")
    state.players["bob"].eliminate()

    active = [p for p in state.players.values() if p.is_active]
    assert len(active) == 1
    assert active[0].id == "alice"
