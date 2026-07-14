"""Drive bot turns for a game over the HTTP API.

Unlike ``love_letter.simulation``, which runs bots in-process against the
real ``GameState`` (bots there can technically see hidden fields), this
module plays fair: bots here only ever see what the API exposes to that
player, so opponents' hidden hands are genuinely unknown.

A driver never touches the engine directly. Any client that can reach the
API — this driver, a human clicking through the GUI, a future LLM bot — is
just another caller of the same endpoints.
"""

from __future__ import annotations

import random
import time
from typing import Callable, Optional

import httpx

Strategy = Callable[[list[dict], dict], dict]

# Consecutive polls with no bot move taken before drive_game gives up.
# A correctly-behaving server always has *someone* actionable each poll
# (a bot or a human); this guards against the client hanging forever if
# the server ever gets stuck in a non-actionable state again.
STALL_LIMIT = 50


def choose_random(actions: list[dict], state: dict) -> dict:
    """Pick any legal action uniformly at random."""
    return random.choice(actions)


def _score_action(action: dict, state: dict) -> int:
    """Score an action using the same heuristics as ``GreedyBot``.

    Opponents' hidden hand cards are ``None`` here (the API redacts them),
    so the value-peeking heuristics silently no-op instead of cheating.
    """
    players_by_id = {p["id"]: p for p in state["players"]}
    score = action["card_in_hand"] * 2

    if action["card_in_hand"] == 1 and action.get("guess") is not None:  # Guard
        score += action["guess"]

    if action["card_in_hand"] == 5 and action.get("target_player"):  # Prince
        target = players_by_id.get(action["target_player"])
        if target and target.get("hand_card") is not None:
            score += target["hand_card"]

    if action["card_in_hand"] == 3 and action.get("target_player"):  # Baron
        target = players_by_id.get(action["target_player"])
        if target and target.get("hand_card") is not None:
            score -= target["hand_card"]

    if action["card_in_hand"] == 9:  # Princess
        score -= 100

    return score


def choose_greedy(actions: list[dict], state: dict) -> dict:
    """Prefer high-value cards; avoid discarding the Princess."""
    scored = [(_score_action(a, state), a) for a in actions]
    top_score = max(s for s, _ in scored)
    top_actions = [a for s, a in scored if s == top_score]
    return random.choice(top_actions)


def choose_spy(actions: list[dict], state: dict) -> dict:
    """Prioritize playing the Spy; otherwise play greedy."""
    spy_actions = [a for a in actions if a["card_in_hand"] == 0]
    if spy_actions:
        return random.choice(spy_actions)
    return choose_greedy(actions, state)


STRATEGIES: dict[str, Strategy] = {
    "random": choose_random,
    "greedy": choose_greedy,
    "heuristic": choose_greedy,
    "spy": choose_spy,
}


def _is_game_over(state: dict) -> Optional[str]:
    """Return the winning player's ID if the game is over, else None."""
    for player in state["players"]:
        if player["favor_tokens"] >= state["favor_token_threshold"]:
            return player["id"]
    return None


def drive_game(
    client: httpx.Client,
    game_id: str,
    bot_assignments: dict[str, str],
    poll_interval: float = 1.0,
    on_turn: Optional[Callable[[dict, dict], None]] = None,
) -> str:
    """Advance every bot-controlled seat's turns until the game ends.

    Seats not present in ``bot_assignments`` are left alone (a human or
    another process is expected to act for them) — the loop just waits
    and re-polls.

    Args:
        client: An ``httpx.Client`` pointed at the running API.
        game_id: The game to drive.
        bot_assignments: Maps player_id -> strategy name (see ``STRATEGIES``).
        poll_interval: Seconds to sleep between polls/turns, for spectator pacing.
        on_turn: Optional callback invoked with (state, action_taken) after
            each bot move, e.g. to print a spectator log.

    Returns:
        The winning player's ID.
    """
    watcher_id = next(iter(bot_assignments))
    stalled_polls = 0

    while True:
        state = client.get(f"/games/{game_id}", params={"player_id": watcher_id}).json()

        winner = _is_game_over(state)
        if winner is not None:
            return winner

        current_id = state["current_player_id"]
        if current_id not in bot_assignments:
            stalled_polls += 1
            _check_not_stalled(stalled_polls, state)
            time.sleep(poll_interval)
            continue

        actions = client.get(
            f"/games/{game_id}/actions", params={"player_id": current_id}
        ).json()
        if not actions:
            stalled_polls += 1
            _check_not_stalled(stalled_polls, state)
            time.sleep(poll_interval)
            continue

        # Score using the acting bot's own view of the state, not the
        # watcher's — otherwise a bot targeting the watcher seat would see
        # the watcher's real hand card, breaking the "only see what the API
        # exposes" guarantee.
        actor_state = client.get(
            f"/games/{game_id}", params={"player_id": current_id}
        ).json()

        strategy = STRATEGIES[bot_assignments[current_id]]
        chosen = strategy(actions, actor_state)

        response = client.post(f"/games/{game_id}/actions", json=chosen)
        response.raise_for_status()
        stalled_polls = 0

        if on_turn is not None:
            on_turn(actor_state, chosen)

        time.sleep(poll_interval)


def _check_not_stalled(stalled_polls: int, state: dict) -> None:
    """Raise if the game hasn't produced a bot move in too many polls."""
    if stalled_polls >= STALL_LIMIT:
        raise RuntimeError(
            f"drive_game stalled: no bot move for {STALL_LIMIT} consecutive "
            f"polls (current_player_id={state.get('current_player_id')!r}, "
            f"round={state.get('round')})"
        )
