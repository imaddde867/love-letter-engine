"""Pydantic schemas for the Love Letter API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from love_letter.models.card import CardType


class CreateGameRequest(BaseModel):
    """Request body for POST /games."""

    player_ids: list[str] = Field(
        ..., min_length=2, max_length=6, description="Player IDs (2-6 players)"
    )


class ActionRequest(BaseModel):
    """Request body for POST /games/{game_id}/actions."""

    player_id: str
    action_type: str = "play_card"
    card_in_hand: CardType
    other_card: CardType
    target_player: Optional[str] = None
    guess: Optional[CardType] = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    message: str
    violations: list[str] = Field(default_factory=list)
