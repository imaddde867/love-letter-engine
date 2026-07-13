"""Prince card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.state import GameState


class PrinceEffect:
    """Resolve Prince card effect: target discards and redraws.

    Choose any player, including yourself. That player discards their
    hand faceup without resolving its effect and draws a new hand.
    If they discard the Princess, they are out and do not draw.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Prince effect to the game state.

        Args:
            state: The current game state.
            action: The Prince action with target_player.

        Returns:
            The updated game state (target may be eliminated).

        Raises:
            ValueError: If target_player is missing.
        """
        if action.target_player is None:
            raise ValueError("Prince requires a target_player")

        target = state.players[action.target_player]

        # Protected players cannot be targeted
        if target.protected_until_next_turn:
            return state

        # Discard target's hand
        discarded_card = target.hand_card
        target.hand_card = None

        # If they discarded the Princess, they are eliminated and don't redraw
        if discarded_card == CardType.PRINCESS:
            target.eliminate()
            return state

        # Redraw from deck or facedown
        target.hand_card = state.draw_card()

        return state
