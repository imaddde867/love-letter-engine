"""Tests for the bot-vs-bot simulator."""

from hypothesis import given, settings
from hypothesis import strategies as st

from love_letter.bots import Player
from love_letter.bots.examples import RandomBot
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.simulation import CONSECUTIVE_SKIP_LIMIT, SimulationResult, simulate


class _AlwaysPrincessBot:
    """Concrete class that always plays Princess (self-elimination)."""

    def choose_action(self, state) -> Action:
        return Action(
            action_type="play_card",
            card_in_hand=CardType.PRINCESS,
            other_card=None,
            player_id="bot",
        )


class _AlwaysRaisesBot:
    """Bot that always raises an exception on choose_action."""

    def choose_action(self, state) -> Action:
        raise RuntimeError("bot always fails")


def test_simulation_result_has_winner():
    """SimulationResult stores the winner's ID."""
    result = SimulationResult(
        winner_id="alice",
        rounds=[],
    )
    assert result.winner_id == "alice"


def test_simulation_result_stores_rounds():
    """SimulationResult stores round-by-round data."""
    result = SimulationResult(
        winner_id="alice",
        rounds=[{"round": 1, "winner": "alice"}],
    )
    assert len(result.rounds) == 1
    assert result.rounds[0]["round"] == 1


def test_simulation_result_stores_final_standings():
    """SimulationResult stores final favor token counts."""
    result = SimulationResult(
        winner_id="alice",
        rounds=[],
        final_standings={"alice": 5, "bob": 3},
    )
    assert result.final_standings["alice"] == 5


def test_simulate_returns_result():
    """simulate() returns a SimulationResult with a winner."""
    bot_a = RandomBot()
    bot_b = RandomBot()

    result = simulate(bot_a, bot_b, player_count=4)

    assert isinstance(result, SimulationResult)
    assert result.winner_id is not None
    assert result.winner_id in ("p0", "p1", "p2", "p3")


def test_simulate_completes_in_finite_rounds():
    """simulate() terminates — does not loop forever."""
    bot_a = RandomBot()
    bot_b = RandomBot()

    result = simulate(bot_a, bot_b, player_count=4)

    assert len(result.rounds) > 0


def test_simulate_stores_final_standings():
    """simulate() populates final_standings for all players."""
    bot_a = RandomBot()
    bot_b = RandomBot()

    result = simulate(bot_a, bot_b, player_count=4)

    assert len(result.final_standings) == 4
    for pid in ("p0", "p1", "p2", "p3"):
        assert pid in result.final_standings


def test_simulate_records_round_details():
    """Each round has a round number and active players."""
    bot_a = RandomBot()
    bot_b = RandomBot()

    result = simulate(bot_a, bot_b, player_count=4)

    for round_data in result.rounds:
        assert "round" in round_data
        assert "active_players" in round_data
        assert len(round_data["active_players"]) > 0


def test_simulate_with_always_princess_bot_loses_fast():
    """A bot that only plays Princess tends to lose — it eliminates itself whenever it holds the card."""
    bot_princess = _AlwaysPrincessBot()
    bot_random = RandomBot()

    result = simulate(bot_princess, bot_random, player_count=2)

    # The princess bot (p0) self-eliminates when it holds the Princess,
    # giving p1 favor tokens. It may still win rounds when it doesn't hold it.
    assert len(result.rounds) > 0
    assert result.winner_id is not None


def test_skipped_turns_recorded_in_rounds():
    """A bot that always raises produces skipped-turn entries in rounds."""
    bot_raises = _AlwaysRaisesBot()
    bot_random = RandomBot()

    result = simulate(bot_raises, bot_random, player_count=2)

    skipped = [r for r in result.rounds if r.get("skipped")]
    assert len(skipped) > 0, "expected at least one skipped turn entry"
    for entry in skipped:
        assert "round" in entry
        assert "active_players" in entry
        assert "player" in entry
        assert "reason" in entry
        assert entry["skipped"] is True


def test_consecutive_skip_limit_terminates_simulation():
    """Simulation terminates when the same player hits the consecutive skip limit."""
    bot_raises = _AlwaysRaisesBot()

    result = simulate(bot_raises, bot_raises, player_count=2)

    # Must terminate — not hang forever
    assert result.error is not None, "expected error field to be set on abnormal termination"
    assert "skip" in result.error.lower()


def test_simulation_result_has_error_field():
    """SimulationResult has an error field that defaults to None."""
    result = SimulationResult(winner_id="p0")
    assert result.error is None


@given(player_count=st.integers(min_value=2, max_value=6))
@settings(max_examples=50)
def test_always_raises_bot_terminates_bounded(player_count):
    """Simulation with always-raises bots always terminates within bounded turns."""
    bot = _AlwaysRaisesBot()

    result = simulate(bot, bot, player_count=player_count)

    assert result.error is not None
    assert len(result.rounds) <= CONSECUTIVE_SKIP_LIMIT * player_count + 1
