"""Tests for the bot-vs-bot simulator."""

from love_letter.bots import Player
from love_letter.bots.examples import RandomBot
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.simulation import SimulationResult, simulate


class _AlwaysPrincessBot:
    """Concrete class that always plays Princess (self-elimination)."""

    def choose_action(self, state) -> Action:
        return Action(
            action_type="play_card",
            card_in_hand=CardType.PRINCESS,
            other_card=None,
            player_id="bot",
        )


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
    assert result.winner_id in ("alice", "bob")


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
    for pid in ("alice", "bob"):
        assert pid in result.final_standings


def test_simulate_records_round_details():
    """Each round has a winner and favor token changes."""
    bot_a = RandomBot()
    bot_b = RandomBot()

    result = simulate(bot_a, bot_b, player_count=4)

    for round_data in result.rounds:
        assert "round" in round_data
        assert "winner_ids" in round_data
        assert len(round_data["winner_ids"]) > 0


def test_simulate_with_always_princess_bot_loses_fast():
    """A bot that only plays Princess loses immediately."""
    bot_princess = _AlwaysPrincessBot()
    bot_random = RandomBot()

    result = simulate(bot_princess, bot_random, player_count=2)

    assert result.winner_id == "bob"
