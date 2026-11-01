# Caching and Performance Interview Cheat Sheet

[Study index](README.md) · Related: [algorithms](Algorithms_Data_Structures.md), [distributed systems](Distributed_Systems.md), [database tuning](../Cheatsheets/Database.md).

Examples illustrate design choices, not universal defaults. Redis commands assume a compatible Redis server; Python fragments omit application collaborators.

## Contents

- [1. When does caching help, and when does it hurt?](#1-when-does-caching-help-and-when-does-it-hurt)
- [2. How does cache-aside work?](#2-how-does-cache-aside-work)
- [3. Why can “update DB, then delete cache” still return stale data?](#3-why-can-update-db-then-delete-cache-still-return-stale-data)
- [4. TTL vs. eviction: what is the difference?](#4-ttl-vs-eviction-what-is-the-difference)
- [5. How do you prevent a cache stampede?](#5-how-do-you-prevent-a-cache-stampede)
- [6. Why use Redis, and how do you scale it?](#6-why-use-redis-and-how-do-you-scale-it)
- [7. How does a CDN work, and what belongs in the cache key?](#7-how-does-a-cdn-work-and-what-belongs-in-the-cache-key)
- [8. What should you measure and test?](#8-what-should-you-measure-and-test)
- [9. Interview answer: Redis TTL, old data removal, and consistency](#9-interview-answer-redis-ttl-old-data-removal-and-consistency)
- [References](#references)

## 1. When does caching help, and when does it hurt?

**Scenario:** a product endpoint repeatedly reads the same catalog rows. Cache reusable, expensive results when their freshness policy is explicit. Start by measuring where time is spent: caching a DB result will not repair a slow external payment call.

| Choice | Advantage | Cost / failure mode |
|---|---|---|
| No cache | Simple freshness model | Repeated computation and source load |
| Local process cache | No network hop | Separate copy per worker; restart loss; invalidation across instances |
| Shared Redis | Shared keys across processes | Network dependency, serialization, capacity and availability management |
| CDN | Serves responses near clients | Correct public/private cache policy and invalidation required |

**Estimate:** if requests are 5,000/s and a measured 90% hit ratio applies, approximately 500 source reads/s remain, excluding refresh traffic. A cache outage can abruptly restore 5,000/s source load. Plan admission control before it happens.

**Dig deeper:** is the hit ratio request-weighted or byte-weighted? Is the hot key too large? How long can users tolerate stale values? Which reads must bypass the cache?

## 2. How does cache-aside work?

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

## 3. Why can “update DB, then delete cache” still return stale data?

Timeline: reader misses → reads old DB value → writer commits new value → writer deletes cache → reader fills old value. A simple invalidation sequence does not make two systems atomic.

| Strategy | Helps with | Remaining limitation |
|---|---|---|
| Bounded TTL | Limits duration of many stale entries | Not instantaneous consistency; stale refill can restart TTL |
| Versioned entries / conditional publish | Reject older versions when version ordering is enforced | Version source and atomic comparison must be correct |
| CDC/event invalidation | All writers can trigger invalidation | Delivery lag, duplicates, and ordering |
| Source-only critical reads | Stronger authoritative decision | Source latency/load |

For money, permissions, or inventory allocation, make the authoritative decision at the database/service boundary. An evictable cache should not be the only location of a critical invariant.

**Dig deeper:** why isn't a delayed second delete a correctness proof? How do you handle a crash between DB commit and invalidation? Could an outbox improve delivery without removing all freshness lag?

## 4. TTL vs. eviction: what is the difference?

TTL expires an entry according to time; eviction removes entries under memory pressure. A 10-minute TTL does not promise an entry stays for 10 minutes. Redis expiration is not a precise business scheduler.

```redis
SET catalog:v2:7:42 '{"name":"Keyboard"}' EX 60
TTL catalog:v2:7:42
DEL catalog:v2:7:42
```

Use jitter, for example `base_ttl + random.randint(0, 15)`, to spread refreshes. If a token or credential has an absolute expiration, bound the cache's TTL by the remaining validity rather than extending validity through jitter.

| Redis policy family | Fit | Tradeoff |
|---|---|---|
| `allkeys-lru` | Evictable cache with recency locality | Approximate recency; not an exact global LRU |
| `allkeys-lfu` | Repeatedly popular keys | Frequency adapts over time; workload-dependent |
| `volatile-*` | Only expiring keys eligible | Non-expiring keys can consume capacity; insufficient candidates can reject writes |
| `noeviction` | Reject memory-growing writes rather than discard keys | Application must handle errors and provision headroom |

Keep durable queues/state separate from expendable cache capacity policies. [Redis eviction reference](https://redis.io/docs/latest/develop/reference/eviction/).

**Dig deeper:** should negative results have shorter TTLs? Does reading extend TTL? Only if the chosen application policy/command does so. What happens to large keys and replication buffers near the memory limit?

## 5. How do you prevent a cache stampede?

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

## 6. Why use Redis, and how do you scale it?

Useful structures include strings for serialized values/counters, hashes for fields, sorted sets for ranked/time-ordered data, and streams for retained events. Choose based on access pattern, not just the presence of Redis in the stack. Pub/Sub has no durable replay for disconnected subscribers; do not mistake it for a durable job queue.

Replication/failover adds availability; sharding distributes keys. Redis Cluster uses **16,384 hash slots**, not a classic consistent-hash ring. Multi-key atomic operations/scripts in a cluster generally require keys in the same slot; hash tags can colocate related keys but can also create hotspots. Check your deployed product/version.

**Dig deeper:** can one giant hot key scale by adding shards? Usually it needs application-level redesign, replication/read offload, or splitting. What durability does your persistence/replication configuration actually provide?

## 7. How does a CDN work, and what belongs in the cache key?

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

## 8. What should you measure and test?

Track hit/miss ratio, cache/source latency, evictions, memory, hot keys, item sizes, refresh failures, and source QPS during cold starts. Test cache unavailability, mass expiry, stale refill races, tenant key collisions, and a source slowdown. Compare endpoint p95/p99 and write cost, not just GET benchmarks.

**Resume drill:** explain the actual process boundary of your “in-memory task cache.” A Python dictionary in one Celery process is not shared automatically with other processes or machines.

## 9. Interview answer: Redis TTL, old data removal, and consistency

**Question:** What is Redis TTL? How do you remove old cached data and keep the cache consistent across application instances?

### TTL and removing old data

TTL (Time To Live) specifies how long a key remains valid. After expiry, Redis treats the key as missing. Redis removes expired keys when accessed and through background expiration checks; physical removal need not happen at the exact expiry instant.

```redis
SET user:123 '{"name":"Merin"}' EX 300
TTL user:123
EXPIRE user:123 600
DEL user:123
```

- `EX 300` sets a five-minute expiry atomically with the value.
- `TTL` returns remaining seconds: `-1` means no expiry; `-2` means the key does not exist.
- `EXPIRE` changes an existing key's expiry to ten minutes from now. Ordinary reads do not extend TTL.
- `DEL` explicitly invalidates the entry, for example after a database update.

| Meaning of “old” | Removal strategy |
|---|---|
| Older than the allowed freshness duration | Set a TTL |
| Database record has changed | Invalidate the corresponding key after commit |
| Redis has reached its configured `maxmemory` limit | Use an eviction policy such as `allkeys-lru` or `allkeys-lfu` |
| Cache schema or dataset version has changed | Switch to a versioned key prefix; expire or clean up the old namespace |

LRU approximates least recently used entries; LFU favors frequently used entries. Neither determines whether a value matches the database. Expiration, memory eviction, and application invalidation solve different problems.

### Consistency across instances

Use the database as the source of truth and a shared Redis cache with cache-aside:

```text
Read:  Redis hit → return value
       Redis miss → read database → cache with TTL → return value

Write: update database → commit → delete corresponding Redis key
```

Delete after commit so readers do not refill from the pre-commit database state simply because invalidation ran too early. All application instances must use the same key conventions, including tenant and version where needed. If they also maintain local caches, those copies need their own invalidation or expiry policy.

This still provides eventual consistency, not an atomic database-and-cache update. A reader can publish an old value after invalidation (see section 3), and a writer can crash after commit but before deleting the cache key.

- **Reliable invalidation:** write an outbox event in the same database transaction, then retry invalidation through a consumer; alternatively, use CDC to capture committed changes. Account for delivery lag and duplicate events.
- **Ordering:** when publishing cached values, use source versions and atomic conditional updates to reject older values. The comparison needs a retained version or watermark; deleting the key and its version alone cannot stop every stale refill.
- **Fallback freshness:** use TTL to limit the lifetime of stale entries. TTL alone does not guarantee a strict bound on source-data age if stale reads can refill the cache.
- **Strictly current decisions:** read from the authoritative database/service using the required transaction and read guarantees. A lagging database replica can also return stale data.

**Concise interview answer:**

> “I would use cache-aside with TTL, update the database first, and invalidate the cache after commit. TTL limits how long cached entries survive, while invalidation refreshes changed data sooner. For reliable invalidation across instances, I would use an outbox or CDC. Concurrent stale refills still need version checks or coordination, so I would describe this as eventual consistency and use the authoritative database for decisions requiring strict consistency.”

## References

- [Redis eviction](https://redis.io/docs/latest/develop/reference/eviction/)
- [Redis Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/)
- [Redis Pub/Sub](https://redis.io/docs/latest/develop/pubsub/)
- [HTTP caching specification](https://www.rfc-editor.org/rfc/rfc9111.html)
