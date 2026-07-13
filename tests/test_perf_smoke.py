"""Perf smoke test: guards against gross regressions in simulation speed.

Not a benchmark - a loose ceiling so an accidental O(n^2) change in the
engine's hot path fails a test instead of silently shipping.
"""

from __future__ import annotations

import time

from love_letter.bots.examples import RandomBot
from love_letter.simulation import simulate

GAMES = 20
MAX_MS_PER_GAME = 20  # ~12x measured local baseline of 1.6ms/game


def test_simulation_throughput_smoke():
    start = time.perf_counter()
    for _ in range(GAMES):
        simulate(RandomBot(), RandomBot(), player_count=4)
    elapsed_ms = (time.perf_counter() - start) * 1000

    ms_per_game = elapsed_ms / GAMES
    assert ms_per_game < MAX_MS_PER_GAME, (
        f"Simulation took {ms_per_game:.1f}ms/game, "
        f"expected < {MAX_MS_PER_GAME}ms/game"
    )
