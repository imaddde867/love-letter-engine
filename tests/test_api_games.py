"""Tests for the API games endpoints."""

import asyncio

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from love_letter.api.app import create_game, get_state
from love_letter.api.schemas import CreateGameRequest


def _run(coro):
    return asyncio.run(coro)


def test_create_game_returns_game_id():
    """POST /games creates a game and returns game_id."""
    data = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    assert "game_id" in data
    assert isinstance(data["game_id"], str)
    assert len(data["game_id"]) > 0


def test_create_game_with_invalid_player_count_fails_validation():
    """POST /games with fewer than 2 players returns validation error."""
    with pytest.raises(ValidationError):
        CreateGameRequest(player_ids=["alice"])


def test_get_state_returns_state_for_existing_game():
    """GET /games/{game_id} returns state for an existing game."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    data = _run(get_state(game_id, player_id="alice"))
    assert data["game_id"] == game_id
    assert "players" in data


def test_get_state_returns_404_for_nonexistent_game():
    """GET /games/{game_id} returns 404 for unknown game."""
    with pytest.raises(HTTPException) as exc_info:
        _run(get_state("nonexistent", player_id="alice"))

    assert exc_info.value.status_code == 404
