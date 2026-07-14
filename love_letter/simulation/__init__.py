"""Bot-vs-bot simulation for Love Letter.

Runs a complete game between two (or more) bots and returns a detailed
result with round-by-round logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from love_letter.bots import Player
from love_letter.engine.engine import Engine
from love_letter.engine.legal_actions import available_actions
from love_letter.models.action import Action
from love_letter.models.state import GameState


CONSECUTIVE_SKIP_LIMIT = 10


@dataclass
class SimulationResult:
    """Outcome of a simulated game.

    Attributes:
        winner_id: ID of the player who reached the favor threshold first.
        rounds: Round-by-round log entries.
        final_standings: Final favor token counts for all players.
        total_rounds: Number of rounds played.
        error: Set to a message if the simulation terminated abnormally.
    """

    winner_id: str
    rounds: list[dict] = field(default_factory=list)
    final_standings: dict[str, int] = field(default_factory=dict)
    total_rounds: int = 0
    error: str | None = None


def simulate(
    bot_a: Player,
    bot_b: Player,
    player_count: int = 4,
) -> SimulationResult:
    """Run a complete game between two bots controlling all seats.

    Each bot is assigned ``player_count // 2`` seats. Bot A controls the
    first half, Bot B the second. The engine advances turns in order and
    each bot chooses actions for its assigned players.

    Args:
        bot_a: First bot instance.
        bot_b: Second bot instance.
        player_count: Total number of players (2-6).

    Returns:
        A ``SimulationResult`` with full round-by-round data.
    """
    if player_count < 2 or player_count > 6:
        raise ValueError(f"player_count must be 2-6, got {player_count}")

    # Assign players to bots
    player_ids = [f"p{i}" for i in range(player_count)]
    mid = player_count // 2
    bot_a_ids = player_ids[:mid] if mid > 0 else player_ids[:1]
    bot_b_ids = player_ids[mid:] if mid > 0 else []

    # Create bots with stateful player_id tracking
    bot_a_tracker = _PlayerTracker(bot_a, bot_a_ids)
    bot_b_tracker = _PlayerTracker(bot_b, bot_b_ids)

    engine = Engine()
    game_id = engine.create_game(player_ids)

    result = SimulationResult(winner_id="", rounds=[], final_standings={})
    round_num = 0
    consecutive_skips: dict[str, int] = {}

    while True:
        state = engine.get_state(game_id, player_ids[0])
        game_over = engine._is_game_over(state)

        if game_over:
            # Find the winner
            threshold = state.favor_token_threshold
            for pid in player_ids:
                if state.players[pid].favor_tokens >= threshold:
                    result.winner_id = pid
                    break
            break

        if engine._is_round_over(state):
            # Record round end
            active = [pid for pid in player_ids if state.players[pid].is_active]
            round_data = {
                "round": round_num,
                "active_players": active,
                "deck_remaining": state.deck_count,
            }
            result.rounds.append(round_data)
            round_num += 1

            # Reset for new round: redraw decks, reinstate players
            engine._start_new_round(state)
            continue

        # Get current player
        active_players = [pid for pid in player_ids if state.players[pid].is_active]
        if not active_players:
            break

        current_idx = state.current_player_index % len(active_players)
        current_player = active_players[current_idx]

        # Bot chooses action
        bot = bot_a_tracker if current_player in bot_a_tracker.ids else bot_b_tracker

        try:
            action = bot.choose_for(current_player, state)
        except Exception as e:
            if _handle_skip(result, consecutive_skips, round_num, active_players, current_player, e):
                break
            state.current_player_index = (state.current_player_index + 1) % len(active_players)
            continue

        # Execute
        try:
            state = engine.execute_action(game_id, current_player, action)
            consecutive_skips[current_player] = 0
        except Exception as e:
            if _handle_skip(result, consecutive_skips, round_num, active_players, current_player, e):
                break
            state.current_player_index = (state.current_player_index + 1) % len(active_players)
            continue

    # Collect final standings
    state = engine.get_state(game_id, player_ids[0])
    result.final_standings = {
        pid: state.players[pid].favor_tokens for pid in player_ids
    }
    result.total_rounds = round_num

    return result


def _handle_skip(
    result: SimulationResult,
    consecutive_skips: dict[str, int],
    round_num: int,
    active_players: list[str],
    player: str,
    exc: Exception,
) -> bool:
    """Record a skipped turn and check the consecutive limit.

    Returns True if the simulation should terminate (limit exceeded).
    """
    result.rounds.append({
        "round": round_num, "active_players": list(active_players),
        "skipped": True, "player": player, "reason": str(exc),
    })
    consecutive_skips[player] = consecutive_skips.get(player, 0) + 1
    if consecutive_skips[player] >= CONSECUTIVE_SKIP_LIMIT:
        result.error = f"Player {player} skipped {CONSECUTIVE_SKIP_LIMIT} consecutive turns"
        return True
    return False


class _PlayerTracker:
    """Wraps a bot and assigns it a set of player IDs."""

    def __init__(self, bot: Player, ids: list[str]):
        self._bot = bot
        self.ids = ids

    def choose_for(self, player_id: str, state: GameState) -> Action:
        """Ask the bot to choose an action for a specific player."""
        if hasattr(self._bot, "set_player_id"):
            self._bot.set_player_id(player_id)
        return self._bot.choose_action(state)


