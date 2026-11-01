# Caching and Performance Interview Cheat Sheet

[Study index](README.md) · Related: [algorithms](Algorithms_Data_Structures.md), [distributed systems](Distributed_Systems.md), [database tuning](../Cheatsheets/Database.md).

Examples illustrate design choices, not universal defaults. Python fragments omit application collaborators; Redis engine details live in its [technology guide](../Cheatsheets/Redis.md).

## Contents

- [1. When does caching help, and when does it hurt?](Caching_Performance.md#when-does-caching-help-and-when-does-it-hurt)
- [2. How does cache-aside work?](Caching_Performance.md#how-does-cache-aside-work)
- [3. Why can “update DB, then delete cache” still return stale data?](Caching_Performance.md#why-can-update-db-then-delete-cache-still-return-stale-data)
- [4. TTL vs. eviction: what is the difference?](Caching_Performance.md#ttl-vs-eviction-what-is-the-difference)
- [5. How do you prevent a cache stampede?](Caching_Performance.md#how-do-you-prevent-a-cache-stampede)
- [7. How does a CDN work, and what belongs in the cache key?](Caching_Performance.md#how-does-a-cdn-work-and-what-belongs-in-the-cache-key)
- [8. What should you measure and test?](Caching_Performance.md#what-should-you-measure-and-test)
- [References](#references)

## When does caching help, and when does it hurt?

**Scenario:** a product endpoint repeatedly reads the same catalog rows. Cache reusable, expensive results when their freshness policy is explicit. Start by measuring where time is spent: caching a DB result will not repair a slow external payment call.

| Choice | Advantage | Cost / failure mode |
|---|---|---|
| No cache | Simple freshness model | Repeated computation and source load |
| Local process cache | No network hop | Separate copy per worker; restart loss; invalidation across instances |
| Shared Redis | Shared keys across processes | Network dependency, serialization, capacity and availability management |
| CDN | Serves responses near clients | Correct public/private cache policy and invalidation required |

**Estimate:** if requests are 5,000/s and a measured 90% hit ratio applies, approximately 500 source reads/s remain, excluding refresh traffic. A cache outage can abruptly restore 5,000/s source load. Plan admission control before it happens.

**Dig deeper:** is the hit ratio request-weighted or byte-weighted? Is the hot key too large? How long can users tolerate stale values? Which reads must bypass the cache?

## How does cache-aside work?

Read cache → on miss read source → populate cache → return. The database remains authoritative.

```python
def get_product(tenant_id, product_id):
    key = f"catalog:v2:{tenant_id}:{product_id}"
    cached = redis_client.get(key)
    if cached is not None:
        return decode(cached)
    product = database.load_product(tenant_id, product_id)
    if product is None:
        return None  # optionally cache a short-lived explicit NOT_FOUND marker
    redis_client.set(key, encode(product), ex=60)
    return product
```

Bound cache connection/read timeouts. This simple example deliberately has no stampede protection and no strong freshness guarantee. Distinguish cache miss, cached null, decoding failure, and cache service failure.

| Pattern | Write behavior | Tradeoff |
|---|---|---|
| Cache-aside | App writes source and invalidates/updates cache | Simple read optimization; races remain |
| Write-through | Write path updates cache/source through a coordinator | Added write latency and coupling; define failure ordering |
| Write-behind | Buffer writes and persist later | Lost writes/reordering risk; unsuitable without durable buffering and recovery |
| Read-through | Cache abstraction loads misses | Centralized loading policy; framework/provider coupling |

**Dig deeper:** two misses load the same item; which value wins? What if deserialization fails after deployment? How do you version keys and prevent cross-tenant collisions?

## Why can “update DB, then delete cache” still return stale data?

Timeline: reader misses → reads old DB value → writer commits new value → writer deletes cache → reader fills old value. A simple invalidation sequence does not make two systems atomic.

| Strategy | Helps with | Remaining limitation |
|---|---|---|
| Bounded TTL | Limits duration of many stale entries | Not instantaneous consistency; stale refill can restart TTL |
| Versioned entries / conditional publish | Reject older versions when version ordering is enforced | Version source and atomic comparison must be correct |
| CDC/event invalidation | All writers can trigger invalidation | Delivery lag, duplicates, and ordering |
| Source-only critical reads | Stronger authoritative decision | Source latency/load |

For money, permissions, or inventory allocation, make the authoritative decision at the database/service boundary. An evictable cache should not be the only location of a critical invariant.

**Dig deeper:** why isn't a delayed second delete a correctness proof? How do you handle a crash between DB commit and invalidation? Could an outbox improve delivery without removing all freshness lag?

For reliable invalidation, record an outbox event with the DB update or capture committed changes through CDC, then retry delivery with stable event identity. Use the same tenant/versioned key scheme across all instances; local cache copies need their own invalidation policy. Version-aware publication needs retained source-version/watermark state: deleting both a cached value and its version cannot reject every delayed stale refill. Strictly current decisions require an authoritative read with the required transaction/read guarantees; a lagging replica can also be stale.

## TTL vs. eviction: what is the difference?

TTL expires an entry according to time; eviction removes entries under memory pressure. Neither proves that a cached value matches its source. A ten-minute TTL does not promise the entry will survive ten minutes or strictly bound source-data age after a stale refill.

Spread refreshes with TTL jitter; when caching a credential/token, cap TTL at remaining validity rather than extending it. Keep durable state separate from expendable capacity policies. Redis-specific commands, expiration behavior, and memory-policy settings are in [Redis](../Cheatsheets/Redis.md#expiration-invalidation-commands-and-eviction).

## How do you prevent a cache stampede?

**Scenario:** a hot key expires and thousands of requests query the DB simultaneously.

| Technique | Benefit | Failure / cost |
|---|---|---|
| Per-key single-flight | One local refresh; others share result | Each process may still refresh independently |
| Distributed refresh lease | Coordinates refresh across workers | Lease expiry and stale holders require care |
| Stale-while-revalidate | Serve bounded stale data during refresh | Unsuitable where stale data violates rules |
| TTL jitter / early refresh | Avoid synchronized expiries | Does not solve one very hot missing key alone |
| Admission control | Protect source during cache failure | Some requests are rejected/degraded |

A refresh owner must use bounded source timeouts. Waiters need their own deadlines and fallback policy; do not make every waiter busy-poll Redis. The cache lease should optimize duplicate work, not serve as the sole protection for financial correctness.

**Dig deeper:** refresh fails for ten minutes—how stale may the value become? How do you prevent a single-flight map itself leaking? What is the behavior on a cold deployment?


## How does a CDN work, and what belongs in the cache key?

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=60, s-maxage=300
ETag: "catalog-v42"
Vary: Accept-Encoding
```

Browser freshness and shared-cache freshness can differ. Put immutable content at versioned URLs; use conservative policy for personalized responses. Include the dimensions that change content, but avoid an unbounded key space. Authentication cookies/headers need explicit treatment by the CDN configuration.

| Policy | Meaning / practical implication |
|---|---|
| `no-store` | Do not store this response |
| `no-cache` | Stored response requires validation before reuse |
| `private` | Intended for a private cache, not a shared cache |
| Versioned asset URL | New bytes get a new URL; easier long-lived caching |

**Dig deeper:** why does a purge not prove every edge is instantly fresh? What prevents private invoices being cached publicly? How do signed URLs expire and interact with cache keys?

## What should you measure and test?

Track hit/miss ratio, cache/source latency, evictions, memory, hot keys, item sizes, refresh failures, and source QPS during cold starts. Test cache unavailability, mass expiry, stale refill races, tenant key collisions, and a source slowdown. Compare endpoint p95/p99 and write cost, not just GET benchmarks.

**Resume drill:** explain the actual process boundary of your “in-memory task cache.” A Python dictionary in one Celery process is not shared automatically with other processes or machines.


## References

- [HTTP caching specification](https://www.rfc-editor.org/rfc/rfc9111.html)
