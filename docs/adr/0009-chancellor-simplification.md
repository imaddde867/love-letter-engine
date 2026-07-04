# ADR-009: Chancellor Simplification for API Surface

## Status

Accepted.

## Context

The original Chancellor card had complex keep/return fields that created
ambiguity in the API contract. The Chancellor doubles the active player's
favor token gain for one round, then they lose double favor tokens at round
end. Modeling both directions required extra fields on `Action` that did not
map cleanly to the JSON request schema.

## Decision

- Simplified Chancellor to a single effect: double favor gain for the actor
  this round.
- Lost double favor at round end is tracked via a flag on `Player`, not an
  action field.
- `Action` no longer needs Chancellor-specific fields beyond the standard
  `card_in_hand` / `other_card`.

## Consequences

- API surface stays clean: `Action` schema is uniform across all cards.
- Engine handles Chancellor internals without exposing them to the client.
- Tests verify doubled favor and correct resolution when only one player
  uses Chancellor.
