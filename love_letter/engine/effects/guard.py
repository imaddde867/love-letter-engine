"""Guard card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class GuardEffect:
    """Resolve Guard card effect: guess target's card.

    The player chooses another player and names a character other than Guard.
    If that player has that card, they are eliminated from the round.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Guard effect to the game state.

        Args:
            state: The current game state.
            action: The Guard action with target_player and guess.

        Returns:
            The updated game state (target may be eliminated).

        Raises:
            ValueError: If target_player or guess is missing.
        """
        target_id = action.target_player
        guess = action.guess

        if target_id is None:
            # No valid target (e.g. every opponent is protected) — no effect.
            return state
        if guess is None:
            raise ValueError("Guard requires a guess (card type)")

        target = state.players[target_id]

        # Protected players cannot be eliminated
        if target.protected_until_next_turn:
            return state

        # Check if target has the guessed card
        if target.hand_card == guess:
            target.eliminate()

        return state
