# ADR-001: Rate Limiting Algorithm Choice

## Status

Accepted

## Context

We need a distributed rate limiter for a multi-node API gateway. Different use cases have different requirements:

- **Billing/quota enforcement** needs simple, predictable counting.
- **API protection** needs smooth, accurate throttling without boundary bursts.
- **Real-time/streaming APIs** need burst tolerance with sustained rate control.

No single algorithm satisfies all three. We must decide whether to support one algorithm well or multiple algorithms behind a common interface.

## Decision

**Support three algorithms behind a unified interface**, selectable per rate limit rule:

1. **Fixed Window Counter** — default for most rules
2. **Sliding Window Log** — for rules requiring precision
3. **Token Bucket** — for rules requiring burst tolerance

Each algorithm is implemented as an atomic Redis Lua script conforming to the same input/output contract:

```
Input:  (key, limit, window_seconds, now_microseconds)
Output: {allowed: bool, remaining: int, reset_at: int}
```

The algorithm is selected at configuration time per rule, not per request. The `RateLimiter` client delegates to the appropriate Lua script based on the resolved config.

### Alternatives Considered

| Alternative | Why rejected |
|---|---|
| **Single algorithm (sliding window only)** | Memory cost too high for high-cardinality keys. Sorted sets with millions of entries per key are expensive. |
| **Leaky bucket** | Functionally similar to token bucket but harder to reason about for burst configuration. No distinct advantage. |
| **Sliding window counter** (hybrid fixed+sliding) | Good middle ground but adds complexity to explain to users. Can be added later as a 4th option if needed. |
| **External rate limiter service (e.g., Envoy, Kong)** | Adds operational complexity and a network hop. We want an embedded library for minimal latency. |

## Consequences

### Positive
- Users pick the right tool for each rule without system-wide compromise.
- Common interface means the application code doesn't care which algorithm runs.
- Each algorithm's Lua script is independently testable and replaceable.

### Negative
- Three Lua scripts to maintain instead of one.
- Operators must understand the trade-offs to configure correctly. Mitigation: good defaults (fixed window) and documentation.
- Slightly more complex config schema (an `algorithm` field per rule).

### Risks
- Algorithm proliferation: resist adding more unless there's a clear use case not served by these three. The interface supports extension, but restraint is key.
