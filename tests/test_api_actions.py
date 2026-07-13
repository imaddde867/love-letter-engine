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


def test_execute_action_on_unknown_game_returns_404():
    """POST /actions with unknown game_id returns 404, not 400."""
    with pytest.raises(HTTPException) as exc_info:
        _run(execute_action(
            "nonexistent-game",
            ActionRequest(
                player_id="alice",
                action_type="play_card",
                card_in_hand=CardType.GUARD,
                other_card=CardType.PRIEST,
            ),
        ))

    assert exc_info.value.status_code == 404


def test_execute_action_on_finished_game_returns_409():
    """POST /actions on a game that already reached the favor threshold returns 409."""
    game_id, _ = _create_game()
    state = engine.get_state(game_id, "alice")
    state.players["alice"].favor_tokens = state.favor_token_threshold
    state.players["alice"].hand_card = CardType.GUARD
    state.deck = [CardType.PRIEST, CardType.BARON]

    with pytest.raises(HTTPException) as exc_info:
        _run(execute_action(
            game_id,
            ActionRequest(
                player_id="alice",
                action_type="play_card",
                card_in_hand=CardType.GUARD,
                other_card=CardType.PRIEST,
                target_player="bob",
                guess=CardType.PRIEST,
            ),
        ))

    assert exc_info.value.status_code == 409


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


def test_action_request_accepts_missing_other_card():
    """ActionRequest defaults other_card to None when omitted."""
    req = ActionRequest(
        player_id="alice",
        card_in_hand=CardType.PRINCESS,
    )
    assert req.other_card is None


def test_princess_discard_via_api_no_other_card():
    """Princess discard works end-to-end without other_card in request."""
    game_id, _ = _create_game()
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.PRINCESS
    state.deck = [CardType.GUARD, CardType.BARON]

    new_state = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            card_in_hand=CardType.PRINCESS,
        ),
    ))
    assert new_state["game_id"] == game_id
    alice = next(p for p in new_state["players"] if p["id"] == "alice")
    assert alice["hand_card"] is None


def test_chancellor_via_api_no_other_card():
    """Chancellor works end-to-end without other_card in request."""
    game_id, _ = _create_game()
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.CHANCELLOR
    state.deck = [CardType.GUARD, CardType.BARON]

    new_state = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            card_in_hand=CardType.CHANCELLOR,
        ),
    ))
    assert new_state["game_id"] == game_id
    alice = next(p for p in new_state["players"] if p["id"] == "alice")
    assert alice["hand_card"] is not None


def test_spy_serializes_as_zero_not_null():
    """SPY (value 0) serializes as 0, not null, in _state_to_dict."""
    game_id, _ = _create_game()
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = CardType.SPY
    state.deck = [CardType.GUARD, CardType.BARON]

    response = _run(get_state(game_id, player_id="alice"))
    alice = next(p for p in response["players"] if p["id"] == "alice")
    assert alice["hand_card"] == 0
