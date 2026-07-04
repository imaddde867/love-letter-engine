"""Spy card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class SpyEffect:
    """Resolve Spy card effect: no immediate effect.

    No immediate effect. At the end of the round, if you are the only
    player still in the round who played or discarded a Spy, gain 1
    extra favor token. This does not replace the normal round winner's
    token. You can gain only 1 Spy token per round.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Spy effect to the game state.

        Args:
            state: The current game state.
            action: The Spy action.

        Returns:
            The updated game state (unchanged, bonus tracked separately).
        """
        # Spy bonus is tracked at round end
        # No immediate state change
        return state
