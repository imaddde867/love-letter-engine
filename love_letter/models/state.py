"""Game state model for Love Letter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from love_letter.models.card import CardType
from love_letter.models.player import Player


@dataclass
class GameState:
    """Complete state of a Love Letter game instance.

    Attributes:
        game_id: Unique identifier for this game.
        round: Current round number (1-indexed).
        deck: Facedown pile of remaining character cards.
        facedown_card: Card set aside at round start (not in deck).
        players: Mapping of player_id to Player objects.
        current_player_index: Index into sorted active players for turn order.
        played_cards: Cards played faceup during the current round.
        favor_token_threshold: Favor tokens needed to win the game.
    """

    game_id: str
    round: int = 1
    deck: list[CardType] = field(default_factory=list)
    facedown_card: Optional[CardType] = None
    players: dict[str, Player] = field(default_factory=dict)
    current_player_index: int = 0
    played_cards: list[dict] = field(default_factory=list)
    favor_token_threshold: int = 4

    @property
    def deck_count(self) -> int:
        """Number of cards remaining in the deck."""
        return len(self.deck)

    def draw_card(self) -> Optional[CardType]:
        """Draw the next card: from the deck, falling back to the facedown card.

        Returns:
            The drawn card, or None if both deck and facedown card are empty.
        """
        if self.deck:
            return self.deck.pop(0)
        if self.facedown_card is not None:
            card = self.facedown_card
            self.facedown_card = None
            return card
        return None
