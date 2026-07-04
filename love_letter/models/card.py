"""Card type definitions for Love Letter."""

from __future__ import annotations

from enum import IntEnum


class CardType(IntEnum):
    """All ten card types in the Love Letter deck.

    Values 0-9 match the official card values. Each member carries its
    name and deck count.
    """

    SPY = 0
    GUARD = 1
    PRIEST = 2
    BARON = 3
    HANDMAID = 4
    PRINCE = 5
    CHANCELLOR = 6
    KING = 7
    COUNTESS = 8
    PRINCESS = 9

    @property
    def count(self) -> int:
        return _CARD_COUNTS[self]

    @property
    def display_name(self) -> str:
        return self.name.title()


_CARD_COUNTS: dict[CardType, int] = {
    CardType.SPY: 2,
    CardType.GUARD: 6,
    CardType.PRIEST: 2,
    CardType.BARON: 2,
    CardType.HANDMAID: 2,
    CardType.PRINCE: 2,
    CardType.CHANCELLOR: 2,
    CardType.KING: 1,
    CardType.COUNTESS: 1,
    CardType.PRINCESS: 1,
}
