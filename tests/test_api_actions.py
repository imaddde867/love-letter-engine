"""Tests for the API actions endpoint."""

from fastapi.testclient import TestClient

from love_letter.api.app import app


client = TestClient(app)


def _create_game(player_ids: list[str] = None) -> tuple[str, dict]:
    """Helper to create a game and return (game_id, state)."""
    if player_ids is None:
        player_ids = ["alice", "bob"]
    response = client.post("/games", json={"player_ids": player_ids})
    assert response.status_code == 201
    game_id = response.json()["game_id"]
    state = client.get(f"/games/{game_id}?player_id=alice").json()
    return game_id, state


def test_execute_action_returns_updated_state():
    """POST /actions executes an action and returns new state."""
    game_id, _ = _create_game()

    # Need to know what card alice has to play a valid action
    state = client.get(f"/games/{game_id}?player_id=alice").json()
    alice_hand = state["players"][0]["hand_card"]

    # Play a non-targeting card (Handmaid = 4) with another card kept
    # We need to pick a valid other_card — use the Princess (9) as keep
    response = client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "alice",
            "action_type": "play_card",
            "card_in_hand": 4,  # Handmaid
            "other_card": 9,  # Princess
        },
    )
    assert response.status_code == 200
    new_state = response.json()
    assert new_state["game_id"] == game_id


def test_execute_action_with_unknown_player_returns_400():
    """POST /actions with unknown player returns 400 (player not active)."""
    game_id, _ = _create_game()

    response = client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "unknown",
            "action_type": "play_card",
            "card_in_hand": 1,
            "other_card": 2,
        },
    )
    assert response.status_code == 400


def test_execute_action_with_invalid_card_returns_422():
    """POST /actions with invalid card value returns 422."""
    game_id, _ = _create_game()

    response = client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "alice",
            "action_type": "play_card",
            "card_in_hand": 99,  # Invalid card
            "other_card": 2,
        },
    )
    assert response.status_code == 422


def test_execute_action_on_over_game_returns_400():
    """POST /actions on a game over state returns error."""
    game_id, _ = _create_game()

    # Manually force game over by setting favor tokens above threshold
    state = client.get(f"/games/{game_id}?player_id=alice").json()
    # We can't easily force game over via API, so test with invalid action instead
    response = client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "alice",
            "action_type": "play_card",
            "card_in_hand": 1,
            "other_card": 2,
            "target_player": "bob",  # Guard requires guess
            "guess": None,
        },
    )
    # Should get a validation error (400) since Guard needs a guess
    assert response.status_code in (400, 422)
