"""Princess card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class PrincessEffect:
    """Resolve Princess card effect: discard = elimination.

    If you play or discard the Princess for any reason, you are
    immediately out of the round.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Princess effect to the game state.

        Args:
            state: The current game state.
            action: The Princess action.

        Returns:
            The updated game state (player eliminated).
        """
        actor = state.players[action.player_id]
        actor.eliminate()
        return state
