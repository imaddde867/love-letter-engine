"""Chancellor card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.state import GameState


class ChancellorEffect:
    """Resolve Chancellor card effect: draw 2, keep 1, return 2 to bottom.

    Draw 2 cards from the deck. From your 3 cards, keep 1 and secretly
    return 2 facedown to the bottom of the deck in any order.
    If only 1 card is in the deck, draw it and return 1.
    If the deck is empty, no effect.
    """

    @staticmethod
    def resolve(state: GameState, action: Action) -> GameState:
        """Apply Chancellor effect to the game state.

        Args:
            state: The current game state.
            action: The Chancellor action.

        Returns:
            The updated game state (hand replaced, deck modified).
        """
        actor = state.players[action.player_id]

        # Draw 2 cards (or fewer if deck is short)
        drawn: list[CardType] = []
        for _ in range(2):
            if state.deck:
                drawn.append(state.deck.pop(0))
            elif state.facedown_card is not None:
                drawn.append(state.facedown_card)
                state.facedown_card = None
                break

        # Player has 3 cards now: original hand + 2 drawn
        # They keep one and return the other two to the bottom
        # The action's other_card is what they keep
        # Only the two non-kept cards return to bottom (not the played card)
        cards_to_return = [c for c in drawn if c != action.other_card]
        for card in cards_to_return:
            state.deck.insert(0, card)  # Bottom of deck

        actor.hand_card = action.other_card
        return state
