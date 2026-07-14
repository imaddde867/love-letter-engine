"""King card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class KingEffect:
    """Resolve King card effect: swap hands with target.

    Choose another player and trade hands with them.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply King effect to the game state.

        Args:
            state: The current game state.
            action: The King action with target_player.

        Returns:
            The updated game state (hands swapped).

        Raises:
            ValueError: If target_player is missing.
        """
        if action.target_player is None:
            # No valid target (e.g. every opponent is protected) — no effect.
            return state

        actor = state.players[action.player_id]
        target = state.players[action.target_player]

        # Protected players cannot be targeted
        if target.protected_until_next_turn:
            return state

        # Swap hands
        actor.hand_card, target.hand_card = target.hand_card, actor.hand_card

        return state
