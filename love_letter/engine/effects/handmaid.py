"""Handmaid card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class HandmaidEffect:
    """Resolve Handmaid card effect: self-protection.

    Until the start of the player's next turn, other players cannot
    choose this player for card effects. No immediate state change.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Handmaid effect to the game state.

        Args:
            state: The current game state.
            action: The Handmaid action.

        Returns:
            The updated game state (unchanged, protection is tracked separately).
        """
        actor = state.players[action.player_id]
        actor.protected_until_next_turn = True
        return state
