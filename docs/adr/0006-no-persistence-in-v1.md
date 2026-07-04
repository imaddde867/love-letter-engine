# No Persistence in V1

The engine stores game state only in memory during runtime. Games are not persisted to disk or database after they end.

This was chosen because V1 focuses on correctness, testability, and bot training. Adding SQLite or file-based persistence would introduce migration complexity and slow down the initial development. In-memory state is faster, simpler to test, and sufficient for the target use cases.

If match history or replay functionality is needed later, persistence can be added as an optional layer without changing the engine's public API. State serialization to JSON can be implemented on top of the existing models.
