"""Tests for the API actions endpoint."""

import asyncio
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from love_letter.api.app import create_game, engine, execute_action, get_state
from love_letter.api.schemas import ActionRequest, CreateGameRequest
from love_letter.models.card import CardType


def _run(coro):
    return asyncio.run(coro)


def _create_game(player_ids: list[str] | None = None) -> tuple[str, dict]:
    """Helper to create a game and return (game_id, state)."""
    created = _run(create_game(CreateGameRequest(player_ids=player_ids or ["alice", "bob"])))
    game_id = created["game_id"]
    state = _run(get_state(game_id, player_id="alice"))
    return game_id, state


def _response_json(response) -> dict:
    return json.loads(response.body.decode())


def test_execute_action_returns_updated_state():
    """POST /actions executes an action and returns new state."""
    game_id, _ = _create_game()
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.HANDMAID
    state.deck = [CardType.PRINCESS, CardType.GUARD]

    new_state = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=CardType.HANDMAID,
            other_card=CardType.PRINCESS,
        ),
    ))
    assert new_state["game_id"] == game_id


def test_execute_action_with_unknown_player_returns_400():
    """POST /actions with unknown player returns 400."""
    game_id, _ = _create_game()

    with pytest.raises(HTTPException) as exc_info:
        _run(execute_action(
            game_id,
            ActionRequest(
                player_id="unknown",
                action_type="play_card",
                card_in_hand=CardType.GUARD,
                other_card=CardType.PRIEST,
            ),
        ))

    assert exc_info.value.status_code == 400


def test_execute_action_with_invalid_card_fails_validation():
    """POST /actions with invalid card value returns validation error."""
    with pytest.raises(ValidationError):
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=99,
            other_card=2,
        )


def test_execute_action_on_invalid_action_returns_400():
    """POST /actions returns structured validation errors."""
    game_id, _ = _create_game()
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.GUARD
    state.deck = [CardType.PRIEST, CardType.BARON]

    response = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=CardType.GUARD,
            other_card=CardType.PRIEST,
            target_player="bob",
            guess=None,
        ),
    ))
    data = _response_json(response)
    assert response.status_code == 400
    assert data["error"] == "invalid_action"
    assert data["violations"] == ["Guard requires a guess (card type)"]
