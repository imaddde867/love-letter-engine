"""Tests for the HTTP-driven bot loop in love_letter.driver."""

import pytest
from fastapi.testclient import TestClient

from love_letter.api.app import app
from love_letter.driver import choose_greedy, choose_random, choose_spy, drive_game


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_choose_random_returns_one_of_the_actions():
    actions = [{"card_in_hand": 1}, {"card_in_hand": 2}]
    assert choose_random(actions, {}) in actions


def test_choose_greedy_avoids_princess_when_alternative_exists():
    state = {"players": []}
    actions = [
        {"card_in_hand": 9, "target_player": None, "guess": None},  # Princess
        {"card_in_hand": 3, "target_player": None, "guess": None},  # Baron
    ]
    chosen = choose_greedy(actions, state)
    assert chosen["card_in_hand"] == 3


def test_choose_greedy_ignores_hidden_opponent_hand():
    """Opponent hand_card is None (redacted) — must not crash or cheat."""
    state = {"players": [{"id": "bob", "hand_card": None}]}
    actions = [{"card_in_hand": 3, "target_player": "bob", "guess": None}]
    chosen = choose_greedy(actions, state)
    assert chosen["card_in_hand"] == 3


def test_choose_spy_prefers_spy_action():
    state = {"players": []}
    actions = [
        {"card_in_hand": 3, "target_player": None, "guess": None},
        {"card_in_hand": 0, "target_player": None, "guess": None},  # Spy
    ]
    chosen = choose_spy(actions, state)
    assert chosen["card_in_hand"] == 0


def test_drive_game_plays_a_full_bot_vs_bot_game(client):
    create_resp = client.post("/games", json={"player_ids": ["alice", "bob"]})
    body = create_resp.json()
    game_id = body["game_id"]
    tokens = body["tokens"]

    winner = drive_game(
        client,
        game_id,
        bot_assignments={"alice": "random", "bob": "greedy"},
        tokens=tokens,
        poll_interval=0,
    )

    assert winner in ("alice", "bob")

    final_state = client.get(
        f"/games/{game_id}",
        params={"player_id": "alice"},
        headers={"Authorization": f"Bearer {tokens['alice']}"},
    ).json()
    winner_tokens = next(
        p["favor_tokens"] for p in final_state["players"] if p["id"] == winner
    )
    assert winner_tokens >= final_state["favor_token_threshold"]


def test_drive_game_crosses_multiple_round_boundaries(client):
    """Regression: the engine must deal a new round, not stall after round 1.

    A 2-player game needs 6 favor tokens to win, and a round rarely awards
    more than 1-2, so reaching the threshold requires several round
    transitions. This is the exact gap 176 passing tests didn't cover.
    """
    create_resp = client.post("/games", json={"player_ids": ["alice", "bob"]})
    body = create_resp.json()
    game_id = body["game_id"]
    tokens = body["tokens"]

    winner = drive_game(
        client,
        game_id,
        bot_assignments={"alice": "random", "bob": "random"},
        tokens=tokens,
        poll_interval=0,
    )

    final_state = client.get(
        f"/games/{game_id}",
        params={"player_id": "alice"},
        headers={"Authorization": f"Bearer {tokens['alice']}"},
    ).json()
    assert final_state["round"] > 1
    assert winner in ("alice", "bob")


def test_drive_game_never_leaks_an_active_opponents_hand_to_the_strategy(client):
    """Regression: strategies must only ever see the *acting* bot's own state.

    Previously drive_game fetched state once as a fixed 'watcher' seat and
    reused it for every bot's turn — so a bot other than the watcher would
    see the watcher's own hand card revealed while scoring Baron/Prince
    targets, contradicting the "only see what the API exposes" guarantee.
    """
    create_resp = client.post("/games", json={"player_ids": ["alice", "bob"]})
    body = create_resp.json()
    game_id = body["game_id"]
    tokens = body["tokens"]

    seen_states = []
    drive_game(
        client,
        game_id,
        bot_assignments={"alice": "greedy", "bob": "greedy"},
        tokens=tokens,
        poll_interval=0,
        on_turn=lambda state, action: seen_states.append((state, action)),
    )

    for state, action in seen_states:
        actor_id = action["player_id"]
        for player in state["players"]:
            if player["id"] != actor_id and player["is_active"]:
                assert player["hand_card"] is None, (
                    f"{actor_id}'s turn leaked {player['id']}'s active hand"
                )


def test_drive_game_calls_on_turn_callback(client):
    create_resp = client.post("/games", json={"player_ids": ["alice", "bob"]})
    body = create_resp.json()
    game_id = body["game_id"]
    tokens = body["tokens"]

    calls = []
    drive_game(
        client,
        game_id,
        bot_assignments={"alice": "random", "bob": "random"},
        tokens=tokens,
        poll_interval=0,
        on_turn=lambda state, action: calls.append(action),
    )

    assert len(calls) > 0


def test_get_state_via_http_rejects_spoofed_player_id():
    """A caller who only knows 'bob' as a string cannot fetch bob's state."""
    with TestClient(app) as c:
        create_resp = c.post("/games", json={"player_ids": ["alice", "bob"]})
        game_id = create_resp.json()["game_id"]

        response = c.get(
            f"/games/{game_id}",
            params={"player_id": "bob"},
            headers={"Authorization": "Bearer guessed-token"},
        )
        assert response.status_code == 403


def test_post_action_via_http_rejects_spoofed_player_id():
    """A caller cannot submit bob's turn over HTTP using only his player_id."""
    with TestClient(app) as c:
        create_resp = c.post("/games", json={"player_ids": ["alice", "bob"]})
        game_id = create_resp.json()["game_id"]

        response = c.post(
            f"/games/{game_id}/actions",
            json={
                "player_id": "bob",
                "action_type": "play_card",
                "card_in_hand": 5,
            },
            headers={"Authorization": "Bearer guessed-token"},
        )
        assert response.status_code == 403


def test_get_state_via_http_requires_authorization_header():
    """Omitting the Authorization header entirely is rejected, not just a bad token."""
    with TestClient(app) as c:
        create_resp = c.post("/games", json={"player_ids": ["alice", "bob"]})
        body = create_resp.json()
        game_id = body["game_id"]

        response = c.get(f"/games/{game_id}", params={"player_id": "alice"})
        assert response.status_code == 422


def test_token_is_not_accepted_as_a_query_parameter_anymore():
    """Regression: a token in the query string must not authorize the request.

    Query strings end up in browser history, proxy access logs, and
    Referer headers — the token must only be honored via the
    Authorization header.
    """
    with TestClient(app) as c:
        create_resp = c.post("/games", json={"player_ids": ["alice", "bob"]})
        body = create_resp.json()
        game_id = body["game_id"]
        token = body["tokens"]["alice"]

        response = c.get(
            f"/games/{game_id}", params={"player_id": "alice", "token": token}
        )
        # No Authorization header supplied — a query-string token must not
        # substitute for one.
        assert response.status_code == 422
