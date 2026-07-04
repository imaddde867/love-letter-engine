"""Player model for Love Letter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from love_letter.models.card import CardType


@dataclass
class Player:
    """A participant in a Love Letter game.

    Attributes:
        id: Unique identifier for this player.
        is_active: Whether the player is still in the current round.
        hand_card: The single hidden card the player is currently holding.
        favor_tokens: Number of favor tokens accumulated across rounds.
        cards_played: Cards that this player has played faceup during the round.
    """

    id: str
    is_active: bool = True
    hand_card: Optional[CardType] = None
    favor_tokens: int = 0
    cards_played: list[CardType] = field(default_factory=list)

    def eliminate(self) -> None:
        """Remove this player from the current round."""
        self.is_active = False

    def add_favor(self) -> None:
        """Award one favor token to this player."""
        self.favor_tokens += 1
