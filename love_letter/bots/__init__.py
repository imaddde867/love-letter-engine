"""Bot interface for Love Letter engine."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from love_letter.models.action import Action
from love_letter.models.state import GameState


@runtime_checkable
class Player(Protocol):
    """A bot that chooses actions for a player in a game.

    Bots receive the full game state and return an Action for their player.
    The engine validates the returned action before executing it.
    """

    def choose_action(self, state: GameState) -> Action: ...
