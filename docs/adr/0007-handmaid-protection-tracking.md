# ADR-007: Handmaid Protection Tracking

## Status

Accepted.

## Context

Phase 2 added Handmaid protection to the engine so that a player who plays
Handmaid cannot be targeted by other cards on their next turn. This is a
correctness prerequisite for the API layer: without it, targeting cards
(Guard guess, Prince swap, Baron steal) could eliminate or interfere with a
player who just played Handmaid, violating the game rules the API promises.

## Decision

- Add `protected_until_next_turn: bool` to `Player`.
- `HandmaidEffect.resolve()` sets this flag on the actor.
- `Engine._resolve_action()` clears it at the start of the protected player's
  turn before drawing and playing.
- Card effects (Guard, Prince, Baron) check this flag and refuse to target
  a protected player.

## Consequences

- Protection is tracked per-player and cleared automatically by the engine.
- Tests cover flag setting, targeting block, and auto-clear at turn start.
- The API layer does not need to know about protection; it is internal to the
  engine.
