# Strict Validation with Specific Error Violations

All actions are validated before execution. Invalid moves return `400 Bad Request` with a list of specific violations, not just a generic error message.

This was chosen over lenient validation (which logs warnings and makes defaults) because it prevents corrupted game state and makes bot debugging easier. The violation list tells bots exactly what's wrong so they can correct their logic.

InvalidActionError includes a `violations` field listing each constraint that was violated (e.g., "target_player is out of round", "card_in_hand not in player's hand").
