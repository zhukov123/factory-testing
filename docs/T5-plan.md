# T5 Plan: Fixed-Window Rate Limiter

## Design Overview
We will implement a fixed‑window rate limiter that allows at most **N** requests per time window for each user. The window is defined by a start timestamp that aligns with the configured window size (e.g., 1 minute). When the current timestamp falls into a new window, the counter for that user is reset.

## API Signature
```go
// allow returns true if the request is permitted, false otherwise.
func allow(userID string, timestamp int64) bool
```
* `userID` – unique identifier of the caller.
* `timestamp` – Unix epoch in milliseconds (or seconds, depending on the code‑base).

## Key Implementation Steps
1. **Data Structure** – Use a map `map[string]*window` where each entry stores:
   - `windowStart int64` – start of the current fixed window.
   - `count int` – number of requests seen in that window.
2. **Window Calculation** – Given a timestamp and a configured `windowSize` (e.g., 60 000 ms), compute the window start as:
   ```go
   start := (timestamp / windowSize) * windowSize
   ```
3. **Allow Logic**
   - Look up the user’s entry.
   - If `windowStart != start`, reset `count = 0` and set `windowStart = start`.
   - If `count < N`, increment `count` and return `true`.
   - Otherwise, return `false`.
4. **Concurrency** – Guard the map with a `sync.RWMutex` (read‑lock for lookup, write‑lock when updating counters). For higher scalability, a sharded lock or `sync.Map` can be considered.
5. **O(1) Average Operations** – All steps above are constant time; resetting the counter only occurs on window rollover, which is still O(1).

## Timeline Estimate
| Milestone | Estimate |
|-----------|----------|
| Draft design & create docs (this file) | 1 hour |
| Implement `allow` function & thread‑safe map | 3 hours |
| Write unit tests for under‑limit, over‑limit, boundary, multi‑user | 2 hours |
| Review, CI integration, documentation polish | 1 hour |
| Final merge to `main` | 30 minutes |

Total: ~7.5 hours.
