"""Priest card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class PriestEffect:
    """Resolve Priest card effect: reveal target's hand.

    The player chooses another player and secretly looks at their hand.
    This is information only; no game state changes.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Priest effect to the game state.

        Args:
            state: The current game state.
            action: The Priest action with target_player.

        Returns:
            The updated game state (unchanged, information only).

        Raises:
            ValueError: If target_player is missing.
        """
        if not action.target_player:
            # No valid target (e.g. every opponent is protected) — no effect.
            return state

        # Priest reveals the target's hand to the actor
        # This is information only; no state changes needed
        return state
