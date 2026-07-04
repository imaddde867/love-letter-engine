"""Countess card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class CountessEffect:
    """Resolve Countess card effect: no immediate effect.

    No effect when played. You must play the Countess if the other
    card in your hand is the King or a Prince. You may also play her
    voluntarily.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Countess effect to the game state.

        Args:
            state: The current game state.
            action: The Countess action.

        Returns:
            The updated game state (unchanged).
        """
        # Countess has no immediate effect
        return state
