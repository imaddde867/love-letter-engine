"""Tests for the API games endpoints."""

import asyncio

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from love_letter.api.app import create_game, engine, get_legal_actions, get_state
from love_letter.api.schemas import CreateGameRequest
from love_letter.models.card import CardType


def _run(coro):
    return asyncio.run(coro)


def test_create_game_returns_game_id():
    """POST /games creates a game and returns game_id."""
    data = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    assert "game_id" in data
    assert isinstance(data["game_id"], str)
    assert len(data["game_id"]) > 0


def test_create_game_returns_a_token_per_player():
    """POST /games issues one auth token per seat."""
    data = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    assert set(data["tokens"]) == {"alice", "bob"}
    assert data["tokens"]["alice"] != data["tokens"]["bob"]


def test_create_game_with_invalid_player_count_fails_validation():
    """POST /games with fewer than 2 players returns validation error."""
    with pytest.raises(ValidationError):
        CreateGameRequest(player_ids=["alice"])


def test_get_state_returns_state_for_existing_game():
    """GET /games/{game_id} returns state for an existing game."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    data = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    assert data["game_id"] == game_id
    assert "players" in data


def test_get_state_returns_404_for_nonexistent_game():
    """GET /games/{game_id} returns 404 for unknown game."""
    with pytest.raises(HTTPException) as exc_info:
        _run(get_state("nonexistent", player_id="alice", token="whatever"))

    assert exc_info.value.status_code == 404


def test_get_state_rejects_wrong_token():
    """GET /games/{game_id} refuses a valid player_id with a mismatched token."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    with pytest.raises(HTTPException) as exc_info:
        _run(get_state(game_id, player_id="alice", token="not-alices-token"))

    assert exc_info.value.status_code == 403


def test_get_state_rejects_another_players_token():
    """Alice cannot read her own hand using bob's real token, or vice versa."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    with pytest.raises(HTTPException) as exc_info:
        _run(get_state(game_id, player_id="alice", token=created["tokens"]["bob"]))

    assert exc_info.value.status_code == 403


def test_get_state_includes_current_player_id():
    """GET /games/{game_id} reports whose turn it is by ID, not just index."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    data = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    assert data["current_player_id"] == "alice"


def test_get_state_hides_other_players_hand_cards():
    """GET /games/{game_id} must not leak an active opponent's hidden hand."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]
    state = engine.get_state(game_id, "alice")
    state.players["bob"].hand_card = CardType.PRINCESS

    data = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    bob = next(p for p in data["players"] if p["id"] == "bob")
    assert bob["hand_card"] is None


def test_get_state_reveals_eliminated_players_hand_card():
    """Eliminated players' hands are public, per the discard-faceup rule."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]
    state = engine.get_state(game_id, "alice")
    state.players["bob"].hand_card = CardType.PRINCESS
    state.players["bob"].eliminate()

    data = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    bob = next(p for p in data["players"] if p["id"] == "bob")
    assert bob["hand_card"] == CardType.PRINCESS.value


def test_get_state_includes_drawn_card_on_your_own_turn():
    """GET /games/{game_id} reveals your drawn_card during your own turn."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    data = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    alice = next(p for p in data["players"] if p["id"] == "alice")
    assert alice["drawn_card"] is not None


def test_get_state_hides_drawn_card_on_someone_elses_turn():
    """GET /games/{game_id} must not leak the deck's next card off-turn.

    Regression: drawn_card is the card about to be drawn — revealing it to
    a player who isn't currently acting exposes deck order (their own next
    draw, and by extension timing information about the round) early.
    """
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]
    state = engine.get_state(game_id, "alice")
    state.current_player_index = 1  # bob's turn

    data = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    alice = next(p for p in data["players"] if p["id"] == "alice")
    assert "drawn_card" not in alice


def test_get_legal_actions_returns_actions_for_player():
    """GET /games/{game_id}/actions lists the acting player's legal moves."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.HANDMAID
    state.deck = [CardType.GUARD]

    actions = _run(
        get_legal_actions(game_id, player_id="alice", token=created["tokens"]["alice"])
    )
    assert len(actions) > 0
    assert all(a["player_id"] == "alice" for a in actions)


def test_get_legal_actions_returns_404_for_nonexistent_game():
    """GET /games/{game_id}/actions returns 404 for unknown game."""
    with pytest.raises(HTTPException) as exc_info:
        _run(get_legal_actions("nonexistent", player_id="alice", token="whatever"))

    assert exc_info.value.status_code == 404


def test_get_legal_actions_rejects_another_players_token():
    """Bob cannot see Alice's legal actions using bob's own real token."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    with pytest.raises(HTTPException) as exc_info:
        _run(
            get_legal_actions(
                game_id, player_id="alice", token=created["tokens"]["bob"]
            )
        )

    assert exc_info.value.status_code == 403
