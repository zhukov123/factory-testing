# Distributed Rate Limiter — Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | **Redis becomes unavailable** — all rate limiting stops working | Medium | High | Local in-memory fallback (fail-open by default). Redis Sentinel/Cluster for HA. Alert on `ratelimiter.fallback.active` gauge. | Infra |
| R2 | **Redis memory exhaustion** — OOM kills or eviction of rate limit keys | Low | High | TTL on all keys ensures automatic cleanup. Monitor `used_memory` vs `maxmemory`. Set `maxmemory-policy` to `volatile-lru` (only evicts keys with TTL). Capacity-plan for worst case: `num_unique_keys × avg_key_size`. | Infra |
| R3 | **Clock skew between gateway nodes** — inconsistent rate decisions | N/A (eliminated) | N/A | All timestamps sourced from Redis `TIME` command inside Lua scripts. Nodes never use local clocks for rate limit math. | Design |
| R4 | **Sliding window memory cost** — sorted sets grow large for high-throughput keys | Medium | Medium | Default to fixed window. Sliding window is opt-in. Document that a key with 10K req/min window uses ~10K sorted set members (~500KB). Monitor per-key memory with `MEMORY USAGE`. | Dev |
| R5 | **Lua script atomicity blocks Redis** — long-running script blocks all other commands | Low | High | Keep scripts under 50 lines, O(1) or O(log N) operations. Sliding window's `ZREMRANGEBYSCORE` is O(log N + M) where M is removed elements — acceptable for reasonable window sizes. Set `lua-time-limit` as safety net. | Dev |
| R6 | **Race condition in fallback mode** — local counters are per-node, total throughput = N × local_limit | Medium | Medium | Document that fallback is approximate. Set `localLimit = globalLimit / expectedNodeCount`. Emit metrics so operators see when fallback is active. | Ops |
| R7 | **Configuration errors** — typo in rule causes wrong limit or no limit | Medium | High | Validate config at startup (fail fast). Schema validation with clear error messages. Log effective config on reload. Dry-run mode for config changes. | Dev |
| R8 | **Key collision** — different rate limit rules produce the same Redis key | Low | High | Key includes algorithm prefix, identifier type, identifier value, and endpoint. Key construction is deterministic and tested. E.g., `rl:fw:user:123:POST /api/orders`. | Dev |
| R9 | **Hot key problem** — single popular API key or endpoint creates Redis hotspot | Medium | Medium | Redis Cluster distributes by key hash slot. If a single key is hot, use client-side caching with short TTL (100ms) for `peekLimit`. For extreme cases, shard the key (split counter across N sub-keys, sum on read). | Dev/Infra |
| R10 | **Latency spike from Redis** — p99 latency exceeds 50ms, slowing all requests | Low | High | 50ms command timeout, automatic fallback to local. Circuit breaker pattern: after N consecutive failures, stop trying Redis for M seconds before probing again. | Dev |
| R11 | **Denial of service via rate limiter** — attacker generates millions of unique keys to exhaust Redis memory | Low | Medium | Cap max distinct keys per prefix. Apply a catch-all rate limit on unauthenticated traffic by IP (coarser granularity, bounded key space). Monitor key count growth rate. | Security |
| R12 | **Upgrade/migration risk** — changing algorithm or window size mid-flight causes inconsistent behavior | Medium | Low | Algorithm change creates new keys (different prefix). Old keys expire naturally via TTL. Document that changing `windowSeconds` mid-window may briefly allow up to 2× limit. | Dev |

---

## Assumptions Requiring Validation

1. **Redis latency < 5ms p99** within the same datacenter. If cross-region, this design needs re-evaluation.
2. **Number of unique rate limit keys < 10M** at any time. Beyond this, Redis memory and sorted set costs need profiling.
3. **Gateway nodes are stateless and horizontally scalable.** The rate limiter library adds no node affinity.
4. **Operators will monitor Redis.** The fallback mode is a safety net, not a long-term operating mode.
5. **Single-region deployment initially.** Multi-region requires a separate design for cross-region counter synchronization.
