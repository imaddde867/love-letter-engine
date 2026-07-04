# ADR-008: Spy Bonus at Round End

## Status

Accepted.

## Context

Phase 2 extended round-end logic to award an extra favor token when exactly
one active player played a Spy during the round. Without this, the Spy card's
information advantage had no mechanical reward beyond the guess itself.

## Decision

- `_end_round()` checks `cards_played` on each active player for `CardType.SPY`.
- If exactly one active player has a Spy in their played cards, they receive
  an additional favor token via `add_favor()`.
- The check happens after the primary winner resolution so it stacks on top.

## Consequences

- Spy is now mechanically meaningful beyond information gathering.
- `cards_played` list on `Player` must be maintained by the engine (done in
  `_resolve_action`).
- Tests cover the single-Spy bonus and no-bonus when multiple players played
  Spy or no one did.
