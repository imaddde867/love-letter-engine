"""Tests for played_cards field in API responses."""

from fastapi.testclient import TestClient

from love_letter.api.app import app


client = TestClient(app)


def test_get_state_includes_played_cards_field():
    """GET /games/{id} must include played_cards in the response."""
    create_response = client.post(
        "/games", json={"player_ids": ["alice", "bob"]}
    )
    game_id = create_response.json()["game_id"]

    response = client.get(f"/games/{game_id}?player_id=alice")
    assert response.status_code == 200
    data = response.json()
    assert "played_cards" in data, (
        "played_cards field is missing from GET /games/{id} response"
    )
    assert isinstance(data["played_cards"], list)


def test_played_cards_populated_after_action():
    """played_cards must be populated after a card is played."""
    create_response = client.post(
        "/games", json={"player_ids": ["alice", "bob"]}
    )
    game_id = create_response.json()["game_id"]

    # Execute an action (play Handmaid - no extra fields needed)
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
    assert "played_cards" in new_state
    assert len(new_state["played_cards"]) == 1

    card_entry = new_state["played_cards"][0]
    assert card_entry["player_id"] == "alice"
    # Card name should be a string matching PLAN spec, not an int
    assert card_entry["card"] == "Handmaid", (
        f"Expected card name 'Handmaid', got {card_entry['card']!r}"
    )


def test_played_cards_multiple_entries():
    """played_cards must accumulate entries across multiple actions."""
    create_response = client.post(
        "/games", json={"player_ids": ["alice", "bob"]}
    )
    game_id = create_response.json()["game_id"]

    # Alice plays Handmaid
    client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "alice",
            "action_type": "play_card",
            "card_in_hand": 4,  # Handmaid
            "other_card": 9,  # Princess
        },
    )

    # Bob plays Countess (no target_player needed)
    response = client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "bob",
            "action_type": "play_card",
            "card_in_hand": 8,  # Countess
            "other_card": 9,  # Princess
        },
    )
    assert response.status_code == 200
    state = response.json()
    assert len(state["played_cards"]) == 2
    assert state["played_cards"][0]["card"] == "Handmaid"
    assert state["played_cards"][1]["card"] == "Countess"


def test_your_id_matches_requesting_player():
    """your_id in the response must match the requesting player."""
    create_response = client.post(
        "/games", json={"player_ids": ["alice", "bob"]}
    )
    game_id = create_response.json()["game_id"]

    response = client.get(f"/games/{game_id}?player_id=bob")
    assert response.status_code == 200
    data = response.json()
    assert "your_id" in data, "your_id field is missing from GET /games/{id} response"
    assert data["your_id"] == "bob"


def test_get_state_after_action_has_both_fields():
    """GET /games/{id} after actions must include both played_cards and your_id."""
    create_response = client.post(
        "/games", json={"player_ids": ["alice", "bob"]}
    )
    game_id = create_response.json()["game_id"]

    # Play a card via POST action
    client.post(
        f"/games/{game_id}/actions",
        json={
            "player_id": "alice",
            "action_type": "play_card",
            "card_in_hand": 4,  # Handmaid
            "other_card": 9,  # Princess
        },
    )

    # GET state for bob - must have both fields
    response = client.get(f"/games/{game_id}?player_id=bob")
    assert response.status_code == 200
    data = response.json()
    assert "played_cards" in data, "played_cards missing from GET response"
    assert "your_id" in data, "your_id missing from GET response"
    assert isinstance(data["played_cards"], list)
    assert len(data["played_cards"]) == 1
    assert data["played_cards"][0]["card"] == "Handmaid"
    assert data["your_id"] == "bob"
