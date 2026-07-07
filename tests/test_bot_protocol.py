"""Tests for the bot protocol."""

from love_letter.engine.engine import Engine
from love_letter.models.card import CardType


def test_player_protocol_exists():
    """Bot protocol is importable from love_letter.bots."""
    from love_letter.bots import Player

    assert Player is not None


def test_player_protocol_has_choose_action():
    """Player protocol requires choose_action."""
    from love_letter.bots import Player

    assert hasattr(Player, "choose_action")


def test_concrete_bot_satisfies_protocol():
    """A simple class with choose_action satisfies the protocol."""
    from typing import runtime_checkable

    from love_letter.bots import Player
    from love_letter.models.action import Action
    from love_letter.models.card import CardType
    from love_letter.models.state import GameState

    class SimpleBot:
        def choose_action(self, state: GameState) -> Action:
            return Action(
                action_type="play_card",
                card_in_hand=CardType.GUARD,
                other_card=CardType.PRIEST,
                player_id="bot",
            )

    bot = SimpleBot()
    assert isinstance(bot, Player)


def _setup_state(hand: CardType, deck_first: CardType | None = None):
    """Helper: create a 2-player game and return (game_id, state)."""
    engine = Engine()
    game_id = engine.create_game(["alice", "bob"])
    state = engine.get_state(game_id, "alice")
    state.players["alice"].hand_card = hand
    if deck_first is not None:
        state.deck = [deck_first] + state.deck
    return game_id, state


def test_spy_bot_choose_action_runs_without_error():
    """SpyBot.choose_action() executes without TypeError."""
    from love_letter.bots.examples import SpyBot

    bot = SpyBot()
    bot.set_player_id("alice")
    game_id, state = _setup_state(CardType.SPY, CardType.GUARD)
    action = bot.choose_action(state)
    assert action.card_in_hand == CardType.SPY


def test_spy_bot_with_no_spy_falls_back_to_greedy():
    """SpyBot without Spy in hand falls back to GreedyBot logic."""
    from love_letter.bots.examples import SpyBot

    bot = SpyBot()
    bot.set_player_id("alice")
    game_id, state = _setup_state(CardType.HANDMAID, CardType.GUARD)
    action = bot.choose_action(state)
    assert action.card_in_hand in (CardType.HANDMAID, CardType.GUARD)


def test_greedy_bot_scores_guard_spy_guess():
    """GreedyBot scores a Guard action guessing SPY (value 0) correctly."""
    from love_letter.bots.examples import GreedyBot
    from love_letter.models.action import Action

    bot = GreedyBot()
    bot.set_player_id("alice")
    game_id, state = _setup_state(CardType.GUARD, CardType.PRIEST)

    action_spy_guess = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
        target_player="bob",
        guess=CardType.SPY,
    )
    action_princess_guess = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
        target_player="bob",
        guess=CardType.PRINCESS,
    )
    score_spy = bot._score_action(action_spy_guess, state)
    score_princess = bot._score_action(action_princess_guess, state)
    assert score_princess > score_spy
