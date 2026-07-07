"""Chancellor card effect implementation."""

from __future__ import annotations

from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.state import GameState
from love_letter.engine.errors import InvalidActionError, Violation


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

        choices = []
        if actor.hand_card is not None and actor.hand_card != CardType.CHANCELLOR:
            choices.append(actor.hand_card)
        choices.extend(drawn)

        if not choices:
            actor.hand_card = action.other_card
            return state

        # Default to keeping the hand card when other_card is unspecified
        kept_card = action.other_card if action.other_card is not None else choices[0]

        if kept_card not in choices:
            raise InvalidActionError([
                Violation(
                    field="other_card",
                    message="Chancellor kept card must be one of the available choices",
                    code="CARD_NOT_AVAILABLE",
                )
            ])

        cards_to_return: list[CardType] = [CardType.CHANCELLOR]
        kept_card_removed = False
        for card in choices:
            if not kept_card_removed and card == kept_card:
                kept_card_removed = True
                continue
            cards_to_return.append(card)

        for card in cards_to_return:
            state.deck.insert(0, card)  # Bottom of deck

        actor.hand_card = kept_card
        return state
