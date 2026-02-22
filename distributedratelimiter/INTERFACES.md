# Distributed Rate Limiter — Interface Contracts

## Public API

### Core Interface

```typescript
interface RateLimiter {
  /**
   * Check whether a request is allowed under the configured rate limits.
   * This is the primary entry point — call before processing each request.
   * Atomically decrements the counter if allowed.
   */
  checkLimit(request: RateLimitRequest): Promise<RateLimitDecision>;

  /**
   * Check limit without decrementing. For read-only quota inspection.
   */
  peekLimit(request: RateLimitRequest): Promise<RateLimitDecision>;

  /**
   * Reload configuration without restarting. Safe to call concurrently.
   */
  reloadConfig(config: RateLimiterConfig): void;

  /**
   * Graceful shutdown: close Redis connections, flush metrics.
   */
  close(): Promise<void>;
}
```

### Request / Response Types

```typescript
interface RateLimitRequest {
  /** The endpoint being accessed, e.g. "POST /api/orders" */
  endpoint: string;

  /** Unique identifier for the caller. At least one of userId, apiKey must be set. */
  userId?: string;
  apiKey?: string;

  /** Cost of this request (default: 1). Use >1 for expensive operations. */
  cost?: number;

  /** Additional labels for rule matching (e.g. { tier: "premium" }) */
  labels?: Record<string, string>;
}

interface RateLimitDecision {
  /** Whether the request is allowed */
  allowed: boolean;

  /** Remaining requests in the current window */
  remaining: number;

  /** Total limit for this window */
  limit: number;

  /** UTC epoch (seconds) when the current window resets */
  resetAt: number;

  /** Seconds to wait before retrying (only set when denied) */
  retryAfter?: number;

  /** Which rule triggered the decision (for debugging) */
  rule: string;

  /** Which backend answered (redis | local) */
  backend: "redis" | "local";
}
```

### HTTP Response Headers

When integrating with an HTTP gateway, map `RateLimitDecision` to these headers:

| Header | Source |
|---|---|
| `X-RateLimit-Limit` | `decision.limit` |
| `X-RateLimit-Remaining` | `decision.remaining` |
| `X-RateLimit-Reset` | `decision.resetAt` |
| `Retry-After` | `decision.retryAfter` (only on 429) |

---

## Configuration Schema

```typescript
interface RateLimiterConfig {
  /** Redis connection settings */
  redis: RedisConfig;

  /** Ordered list of rate limit rules (first match wins within each scope) */
  rules: RateLimitRule[];

  /** Default rule applied when no specific rule matches */
  defaultRule: RateLimitRuleBody;

  /** Behavior when Redis is unavailable */
  fallback: FallbackConfig;

  /** Observability hooks */
  observability?: ObservabilityConfig;
}

interface RedisConfig {
  /** Redis URL, e.g. "redis://host:6379" or "redis-sentinel://host:26379" */
  url: string;

  /** Connection timeout in milliseconds (default: 50) */
  connectTimeoutMs?: number;

  /** Command timeout in milliseconds (default: 50) */
  commandTimeoutMs?: number;

  /** Connection pool size (default: 10) */
  poolSize?: number;

  /** Key prefix for all rate limiter keys (default: "rl:") */
  keyPrefix?: string;
}

interface RateLimitRule {
  /** Human-readable name for this rule (used in Decision.rule and logs) */
  name: string;

  /** Match conditions — all specified fields must match */
  match: {
    endpoint?: string;    // glob pattern, e.g. "POST /api/*"
    userId?: string;      // exact or "*" for any authenticated user
    apiKey?: string;      // exact or "*" for any API key
    labels?: Record<string, string>;
  };

  /** The rate limit parameters */
  rate: RateLimitRuleBody;
}

interface RateLimitRuleBody {
  /** Algorithm to use */
  algorithm: "fixed_window" | "sliding_window" | "token_bucket";

  /** Maximum requests allowed in the window */
  limit: number;

  /** Window duration in seconds (not used for token_bucket) */
  windowSeconds?: number;

  /** Tokens added per second (token_bucket only) */
  refillRate?: number;

  /** Maximum burst size (token_bucket only, defaults to limit) */
  burstSize?: number;
}

interface FallbackConfig {
  /** What to do when Redis is unavailable */
  mode: "allow" | "deny" | "local";

  /** For mode "local": per-node limit (should be total_limit / expected_node_count) */
  localLimit?: number;

  /** For mode "local": window in seconds */
  localWindowSeconds?: number;
}

interface ObservabilityConfig {
  /** Enable metrics emission */
  metricsEnabled?: boolean;

  /** Custom metrics reporter (default: no-op) */
  metricsReporter?: MetricsReporter;

  /** Structured logger instance */
  logger?: Logger;
}
```

---

## Metrics Reporter Interface

```typescript
interface MetricsReporter {
  incrementCounter(name: string, value: number, labels: Record<string, string>): void;
  recordHistogram(name: string, value: number, labels: Record<string, string>): void;
  setGauge(name: string, value: number, labels: Record<string, string>): void;
}
```

---

## Logger Interface

```typescript
interface Logger {
  info(message: string, context?: Record<string, unknown>): void;
  warn(message: string, context?: Record<string, unknown>): void;
  error(message: string, context?: Record<string, unknown>): void;
}
```

---

## Redis Lua Script Contract

All algorithm Lua scripts share this contract:

```
KEYS[1] = rate limit key (fully qualified, e.g. "rl:fw:user:123:POST /api/orders")

ARGV[1] = limit (integer)
ARGV[2] = window_seconds (integer, ignored for token bucket)
ARGV[3] = cost (integer, default 1)
ARGV[4] = refill_rate (float, token bucket only)
ARGV[5] = burst_size (integer, token bucket only)

Returns: [allowed (0|1), remaining (int), reset_at_epoch (int)]
```

Timestamps are obtained inside the script via `redis.call('TIME')` — never passed from the client.

---

## Factory Function

```typescript
/**
 * Create a configured RateLimiter instance.
 * Connects to Redis, uploads Lua scripts, validates config.
 * Throws on invalid config. Redis connection failures are non-fatal
 * (activates fallback mode).
 */
function createRateLimiter(config: RateLimiterConfig): Promise<RateLimiter>;
```

---

## Example Config (YAML)

```yaml
redis:
  url: "redis://redis-primary:6379"
  connectTimeoutMs: 50
  commandTimeoutMs: 50
  poolSize: 10
  keyPrefix: "rl:"

defaultRule:
  algorithm: fixed_window
  limit: 100
  windowSeconds: 60

rules:
  - name: "auth-endpoints"
    match:
      endpoint: "POST /auth/*"
    rate:
      algorithm: sliding_window
      limit: 10
      windowSeconds: 60

  - name: "premium-users"
    match:
      userId: "*"
      labels:
        tier: "premium"
    rate:
      algorithm: token_bucket
      limit: 1000
      refillRate: 20
      burstSize: 100

  - name: "free-api-keys"
    match:
      apiKey: "*"
      labels:
        tier: "free"
    rate:
      algorithm: fixed_window
      limit: 60
      windowSeconds: 60

fallback:
  mode: local
  localLimit: 25
  localWindowSeconds: 60

observability:
  metricsEnabled: true
```
