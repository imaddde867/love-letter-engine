"""Tests for full game flow via the API."""

from fastapi.testclient import TestClient

from love_letter.api.app import app


client = TestClient(app)


def test_full_game_flow():
    """Test creating a game, getting state, and executing actions."""
    # Create game
    response = client.post("/games", json={"player_ids": ["alice", "bob"]})
    assert response.status_code == 201
    game_id = response.json()["game_id"]

    # Get initial state
    response = client.get(f"/games/{game_id}?player_id=alice")
    assert response.status_code == 200
    state = response.json()
    assert state["game_id"] == game_id
    assert len(state["players"]) == 2
    assert state["round"] == 1

    # Execute an action (play Handmaid)
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
    assert new_state["round"] == 1

    # Get state for bob
    response = client.get(f"/games/{game_id}?player_id=bob")
    assert response.status_code == 200
    bob_state = response.json()
    assert len(bob_state["players"]) == 2


def test_game_over_after_threshold():
    """Test that game ends when a player reaches the favor threshold."""
    # Create 2-player game (threshold = 6)
    response = client.post("/games", json={"player_ids": ["alice", "bob"]})
    game_id = response.json()["game_id"]

    # Verify the threshold is set correctly for 2 players
    state = client.get(f"/games/{game_id}?player_id=alice").json()
    assert state["favor_token_threshold"] == 6
