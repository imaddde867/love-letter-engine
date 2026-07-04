"""Baron card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class BaronEffect:
    """Resolve Baron card effect: compare hands, lower eliminated.

    The player chooses another player and secretly compares hands.
    The lower-value card is eliminated. Ties result in no effect.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Baron effect to the game state.

        Args:
            state: The current game state.
            action: The Baron action with target_player.

        Returns:
            The updated game state (one player may be eliminated).

        Raises:
            ValueError: If target_player is missing.
        """
        if not action.target_player:
            raise ValueError("Baron requires a target_player")

        actor = state.players[action.player_id]
        target = state.players[action.target_player]

        # Protected players cannot be eliminated
        if target.protected_until_next_turn:
            return state

        actor_value = actor.hand_card.value
        target_value = target.hand_card.value

        if actor_value < target_value:
            actor.eliminate()
        elif target_value < actor_value:
            target.eliminate()
        # Tie: nothing happens

        return state
