# Phase 2 Review: API Layer Completion

## Against PLAN Success Criteria

### Completed

1. **All card effects implemented and tested** - Phase 1 delivered the card effects; Phase 2 added missing rule behavior needed by the API.
2. **Property tests pass for game invariants** - Existing property tests remain green.
3. **API endpoints work** - Phase 2 exposes:
   - `POST /games`
   - `GET /games/{game_id}`
   - `POST /games/{game_id}/actions`
4. **Error handling returns specific violations** - Invalid actions return structured 400 responses with violation messages.
5. **Code is clean, minimal, and organized** - The API layer is small, and card behavior stays in engine/effect modules.

### Deferred

1. **Bot-vs-bot simulation** - Phase 3 scope.
2. **`available_actions` response field** - Not implemented yet. It needs a richer legal-action generator and belongs with bot/simulation work.

## What We Built

### API Layer (`love_letter/api/`)

- FastAPI app with game creation, state retrieval, and action execution endpoints.
- Pydantic request schemas for game creation and actions.
- JSON state serialization including `your_id`, `played_cards`, and the requesting player's `drawn_card`.
- Structured invalid-action responses.

### Engine Improvements

- `Action` is a Pydantic model for API request compatibility.
- Handmaid protection is tracked in engine state and respected by targeting effects.
- Spy bonus is awarded at round end.
- Prince target validation is covered by the structured validation layer.
- Non-Chancellor actions are checked against the player's actual hand plus drawn card before mutating state.
- Played-card history includes `target_player` when present.

### Dependency Reproducibility

- API/test dependencies are declared under the `test` extra.
- FastAPI, Starlette/AnyIO, HTTPX, Uvicorn, pytest, and Hypothesis are resolved in `uv.lock`.

## Verification

```bash
.venv/bin/python -m pytest -q
```

Result: `115 passed in 0.79s`.

## Remaining Risks

- The API currently exposes enough state for engine/bot iteration, including a `drawn_card` preview for the requesting player. A future player-facing UI may need stricter hidden-information filtering.
- Chancellor keeps the simplified action shape documented in ADR-009; deeper Chancellor choice modeling can be revisited if the API needs exact tabletop ordering semantics.
