"""Tests for full game flow via the API."""

import asyncio

from love_letter.api.app import create_game, engine, execute_action, get_state
from love_letter.api.schemas import ActionRequest, CreateGameRequest
from love_letter.models.card import CardType


def _run(coro):
    return asyncio.run(coro)


def test_full_game_flow():
    """Test creating a game, getting state, and executing actions."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]
    tokens = created["tokens"]

    state = _run(get_state(game_id, player_id="alice", token=tokens["alice"]))
    assert state["game_id"] == game_id
    assert len(state["players"]) == 2
    assert state["round"] == 1

    engine_state = engine.get_state(game_id, "alice")
    engine_state.players["alice"].hand_card = CardType.HANDMAID
    engine_state.deck = [CardType.PRINCESS, CardType.GUARD]

    new_state = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            token=tokens["alice"],
            action_type="play_card",
            card_in_hand=CardType.HANDMAID,
            other_card=CardType.PRINCESS,
        ),
    ))
    assert new_state["round"] == 1

    bob_state = _run(get_state(game_id, player_id="bob", token=tokens["bob"]))
    assert len(bob_state["players"]) == 2


def test_game_over_after_threshold():
    """Test that two-player games use the expected favor threshold."""
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    game_id = created["game_id"]

    state = _run(get_state(game_id, player_id="alice", token=created["tokens"]["alice"]))
    assert state["favor_token_threshold"] == 6
