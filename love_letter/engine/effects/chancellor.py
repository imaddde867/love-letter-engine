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
        drawn = []
        for _ in range(2):
            if state.deck:
                drawn.append(state.deck.pop(0))

        if not drawn:
            actor.hand_card = action.other_card
            return state

        candidates = [actor.hand_card, *drawn]
        keep_card = action.chancellor_keep_card or action.other_card

        cards_to_return = list(candidates)
        if keep_card in cards_to_return:
            cards_to_return.remove(keep_card)
        else:
            raise ValueError("Chancellor keep card must be one of the available cards")

        return_order = action.chancellor_return_order or cards_to_return
        if sorted(return_order) != sorted(cards_to_return):
            raise ValueError("Chancellor return order must match the returned cards")

        state.deck.extend(return_order)
        actor.hand_card = keep_card
        return state
