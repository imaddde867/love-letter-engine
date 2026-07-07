"""Tests for the bot protocol."""


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
