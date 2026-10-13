"""Tests for played_cards field in API responses."""

import asyncio

from love_letter.api.app import create_game, engine, execute_action, get_state
from love_letter.api.schemas import ActionRequest, CreateGameRequest
from love_letter.models.card import CardType


def _run(coro):
    return asyncio.run(coro)


def _bearer(token: str) -> str:
    return f"Bearer {token}"


def _create_game() -> tuple[str, dict]:
    created = _run(create_game(CreateGameRequest(player_ids=["alice", "bob"])))
    return created["game_id"], created["tokens"]


def _set_turn_cards(game_id: str, player_id: str, hand: CardType, drawn: CardType) -> None:
    state = engine.get_state(game_id, player_id)
    state.players[player_id].hand_card = hand
    state.deck = [drawn, CardType.GUARD, CardType.PRIEST]


def test_get_state_includes_played_cards_field():
    """GET /games/{id} must include played_cards in the response."""
    game_id, tokens = _create_game()

    data = _run(get_state(game_id, player_id="alice", authorization=_bearer(tokens["alice"])))
    assert "played_cards" in data
    assert isinstance(data["played_cards"], list)


def test_played_cards_populated_after_action():
    """played_cards must be populated after a card is played."""
    game_id, tokens = _create_game()
    _set_turn_cards(game_id, "alice", CardType.HANDMAID, CardType.PRINCESS)

    new_state = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=CardType.HANDMAID,
            other_card=CardType.PRINCESS,
        ),
        authorization=_bearer(tokens["alice"]),
    ))
    assert len(new_state["played_cards"]) == 1

    card_entry = new_state["played_cards"][0]
    assert card_entry["player_id"] == "alice"
    assert card_entry["card"] == "Handmaid"


def test_played_cards_multiple_entries():
    """played_cards must accumulate entries across multiple actions."""
    game_id, tokens = _create_game()
    _set_turn_cards(game_id, "alice", CardType.HANDMAID, CardType.PRINCESS)

    _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=CardType.HANDMAID,
            other_card=CardType.PRINCESS,
        ),
        authorization=_bearer(tokens["alice"]),
    ))

    _set_turn_cards(game_id, "bob", CardType.COUNTESS, CardType.PRINCESS)
    state = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="bob",
            action_type="play_card",
            card_in_hand=CardType.COUNTESS,
            other_card=CardType.PRINCESS,
        ),
        authorization=_bearer(tokens["bob"]),
    ))
    assert len(state["played_cards"]) == 2
    assert state["played_cards"][0]["card"] == "Handmaid"
    assert state["played_cards"][1]["card"] == "Countess"


def test_your_id_matches_requesting_player():
    """your_id in the response must match the requesting player."""
    game_id, tokens = _create_game()

    data = _run(get_state(game_id, player_id="bob", authorization=_bearer(tokens["bob"])))
    assert data["your_id"] == "bob"


def test_get_state_after_action_has_both_fields():
    """GET /games/{id} after actions must include both played_cards and your_id."""
    game_id, tokens = _create_game()
    _set_turn_cards(game_id, "alice", CardType.HANDMAID, CardType.PRINCESS)

    _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=CardType.HANDMAID,
            other_card=CardType.PRINCESS,
        ),
        authorization=_bearer(tokens["alice"]),
    ))

    data = _run(get_state(game_id, player_id="bob", authorization=_bearer(tokens["bob"])))
    assert "played_cards" in data
    assert "your_id" in data
    assert len(data["played_cards"]) == 1
    assert data["played_cards"][0]["card"] == "Handmaid"
    assert data["your_id"] == "bob"


def test_played_cards_include_target_player_when_present():
    """played_cards entries include target_player to match the PLAN contract."""
    game_id, tokens = _create_game()
    _set_turn_cards(game_id, "alice", CardType.GUARD, CardType.PRIEST)
    # Guess deliberately wrong so bob survives — a correct guess would
    # eliminate him, end the round, and reset played_cards for round 2.
    engine.get_state(game_id, "bob").players["bob"].hand_card = CardType.KING

    response = _run(execute_action(
        game_id,
        ActionRequest(
            player_id="alice",
            action_type="play_card",
            card_in_hand=CardType.GUARD,
            other_card=CardType.PRIEST,
            target_player="bob",
            guess=CardType.BARON,
        ),
        authorization=_bearer(tokens["alice"]),
    ))

    played_card = response["played_cards"][0]
    assert played_card["target_player"] == "bob"
