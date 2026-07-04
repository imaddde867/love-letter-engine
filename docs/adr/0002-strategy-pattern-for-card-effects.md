# Strategy Pattern for Card Effect Resolution

Each card's effect is implemented as a separate class following the Strategy Pattern, not as branches in a single switch statement.

This means `GuardEffect`, `PriestEffect`, `BaronEffect`, etc. each have their own `resolve(state, action)` method. New cards are added by creating new classes, not by modifying existing code.

A monolithic `resolve_card()` function with if/elif branches was considered but rejected because it makes individual effect testing harder and violates the Open/Closed Principle when adding new cards.
