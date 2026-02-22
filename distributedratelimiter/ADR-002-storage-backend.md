# ADR-002: Storage Backend Selection

## Status

Accepted

## Context

The rate limiter needs shared state across multiple gateway nodes. Requests to the same key may arrive at any node, so counters must be globally consistent. The storage must support:

- Atomic read-modify-write operations (no race conditions)
- Sub-millisecond latency (rate check is in the hot path)
- TTL-based key expiration (automatic cleanup)
- High throughput (100K+ ops/sec)
- Operational simplicity

## Decision

**Use Redis as the primary storage backend.**

Specifically:
- All rate limit logic runs as **atomic Lua scripts** via `EVALSHA`, eliminating round-trip race conditions.
- Timestamps are sourced from **`redis.call('TIME')`** inside Lua scripts, not from gateway nodes, eliminating clock skew.
- Key expiration uses Redis `PEXPIRE` / `EXPIREAT` for automatic cleanup.
- Deployment: **Redis Sentinel** (for HA with automatic failover) or **Redis Cluster** (for horizontal scaling).

A **local in-memory fallback** (per-node token bucket) activates when Redis is unreachable, ensuring the gateway never blocks on a storage failure.

### Alternatives Considered

| Alternative | Pros | Cons | Verdict |
|---|---|---|---|
| **Memcached** | Fast, simple | No Lua scripting → can't do atomic read-modify-write. No sorted sets for sliding window. | Rejected |
| **DynamoDB / Cassandra** | Durable, scalable | Too slow for hot-path rate checks (single-digit ms at best). Overkill for ephemeral counters. | Rejected |
| **Hazelcast / In-memory data grid** | No external dependency | Adds JVM dependency. Cluster management complexity. Less battle-tested for this use case. | Rejected |
| **etcd / Consul** | Strong consistency | Designed for config, not high-throughput counters. Write throughput too low. | Rejected |
| **Local memory only (no shared state)** | Zero latency, no dependency | Limits are per-node, not global. A user hitting N nodes gets N× the limit. Only acceptable as fallback. | Fallback only |
| **Redis + local hybrid (write-behind)** | Reduces Redis calls | Complexity of sync logic. Stale local state can allow over-limit. | Deferred — can add as optimization later |

## Consequences

### Positive
- Redis is ubiquitous, well-understood, and already in most infrastructure stacks.
- Lua scripts give us atomic multi-step operations without distributed locks.
- Server-side `TIME` command eliminates clock skew concerns entirely.
- TTL-based expiration means no garbage collection logic needed.
- Operational tooling (monitoring, backup, failover) is mature.

### Negative
- Redis is an additional infrastructure dependency. Mitigated by local fallback mode.
- Redis is single-threaded per shard. For extreme throughput (>500K ops/sec), Redis Cluster sharding is required.
- Data is ephemeral (lost on restart without persistence). Acceptable — rate limit counters are transient by nature. A restart effectively resets all windows, which is a brief period of over-allowing.

### Risks
- **Redis becomes SPOF:** Mitigated by Sentinel/Cluster HA + local fallback.
- **Redis memory growth:** Mitigated by TTL on all keys. Monitor `used_memory` metric.
- **Lua script complexity:** Keep scripts minimal (<50 lines each). Unit test with embedded Redis.
