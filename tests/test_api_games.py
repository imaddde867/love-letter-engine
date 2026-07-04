"""Tests for the API games endpoints."""

from fastapi.testclient import TestClient

from love_letter.api.app import app


client = TestClient(app)


def test_create_game_returns_201_and_game_id():
    """POST /games creates a game and returns 201 with game_id."""
    response = client.post("/games", json={"player_ids": ["alice", "bob"]})
    assert response.status_code == 201
    data = response.json()
    assert "game_id" in data
    assert isinstance(data["game_id"], str)
    assert len(data["game_id"]) > 0


def test_create_game_with_invalid_player_count_returns_422():
    """POST /games with fewer than 2 players returns validation error."""
    response = client.post("/games", json={"player_ids": ["alice"]})
    assert response.status_code == 422


def test_get_state_returns_200_for_existing_game():
    """GET /games/{game_id} returns state for an existing game."""
    create_response = client.post(
        "/games", json={"player_ids": ["alice", "bob"]}
    )
    game_id = create_response.json()["game_id"]

    response = client.get(f"/games/{game_id}?player_id=alice")
    assert response.status_code == 200
    data = response.json()
    assert data["game_id"] == game_id
    assert "players" in data


def test_get_state_returns_404_for_nonexistent_game():
    """GET /games/{game_id} returns 404 for unknown game."""
    response = client.get("/games/nonexistent?player_id=alice")
    assert response.status_code == 404
