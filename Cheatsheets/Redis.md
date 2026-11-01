# Redis interview preparation

[Repository guide](../README.md) · Related: [caching design](../System_Design/Caching_Performance.md), [Celery](Celery.md), [database fundamentals](Database.md).

Use this guide for Redis mechanics. Cache-aside, stale-refill races, stampede prevention, and CDN policy are explained in the caching-design guide rather than repeated here. Verify features against the deployed Redis product/version.

## Contents

- [Data structures and workload fit](#data-structures-and-workload-fit)
- [Does Redis use threads?](#does-redis-use-threads)
- [Expiration, invalidation commands, and eviction](#expiration-invalidation-commands-and-eviction)
- [Replication, failover, and sharding](#replication-failover-and-sharding)
- [Persistence and recovery](#persistence-and-recovery)
- [Latency, security, and operations](#latency-security-and-operations)
- [Interview drills](#interview-drills)
- [References](#references)

## Data structures and workload fit

| Structure | Typical use | Design concern |
|---|---|---|
| String | Serialized cache value, counter | Size, serialization, expiry |
| Hash | Named fields of a record | Growth, atomic operation boundaries |
| List | Ordered values / queue-like primitives | A raw list is not a complete reliable task system |
| Set | Unique membership | Cardinality and memory |
| Sorted set | Ranked or time-ordered values | Scores, ties, memory |
| Stream | Retained event entries and consumer-group processing | Acknowledgement, pending work, retention, recovery |

Pub/Sub broadcasts to connected subscribers without durable replay for disconnected subscribers. Streams add retained entries and progress features but still need application recovery and side-effect idempotency. A Celery broker, result backend, and application cache are distinct roles even when all use Redis.

## Does Redis use threads?

**Short answer:** Redis can use threads, but normal command execution is mostly single-threaded per server process. The event loop handles client requests sequentially; this keeps individual Redis commands atomic, but one slow/blocking command can delay other clients. Redis also uses background threads for selected I/O or persistence work, and supported versions can use I/O threads for socket read/write work. That does not mean arbitrary Redis commands execute in parallel.

| Question | Answer |
|---|---|
| Can multiple application threads use Redis? | Yes. Clients can connect concurrently; use the client library's supported connection/pool behavior. |
| Do Redis commands run in parallel on one instance? | Generally, command execution is serialized on the main thread. |
| Does Redis use any threads? | Yes, for selected background and I/O work; details depend on version/configuration. |
| How to scale command throughput? | Keep commands fast, pipeline to reduce network round trips, and use multiple shards/instances when appropriate. |
| Is one command atomic? | A command executes without another command interleaving on that server. A sequence of commands needs a transaction/script/other coordination when it must be indivisible. |

Redis transactions (`MULTI`/`EXEC`) queue and execute commands together without other clients' commands interleaving, but they do not provide SQL-style rollback of earlier commands when a command has a runtime error. `WATCH` enables optimistic check-and-set workflows. Use Lua/functions for server-side atomic logic when appropriate, and avoid long/blocking commands.


## Expiration, invalidation commands, and eviction

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

| Redis policy family | Fit | Tradeoff |
|---|---|---|
| `allkeys-lru` | Evictable cache with recency locality | Approximate recency; not an exact global LRU |
| `allkeys-lfu` | Repeatedly popular keys | Frequency adapts over time; workload-dependent |
| `volatile-*` | Only expiring keys eligible | Non-expiring keys can consume capacity; insufficient candidates can reject writes |
| `noeviction` | Reject memory-growing writes rather than discard keys | Application must handle errors and provision headroom |

Keep durable queues/state separate from expendable cache eviction policies. Evicting broker keys can break task delivery. Budget replication/client buffers and process overhead as well as dataset memory. [Eviction policies](https://redis.io/docs/latest/develop/reference/eviction/).

## Replication, failover, and sharding

Replication/failover adds availability; sharding distributes keys. Redis Cluster uses **16,384 hash slots**, not a classic consistent-hash ring. Multi-key atomic operations/scripts in a cluster generally require keys in the same slot; hash tags can colocate related keys but can also create hotspots. Check your deployed product/version.

**Dig deeper:** can one giant hot key scale by adding shards? Usually it needs application-level redesign, replication/read offload, or splitting. What durability does your persistence/replication configuration actually provide?

Replication is not a historical backup and does not automatically guarantee zero acknowledged-write loss on failover. Clients need appropriate primary discovery/cluster support and must handle reconnection and ambiguous write outcomes. Test the exact persistence, replication, and failover settings.

## Persistence and recovery

RDB snapshots capture a point-in-time dataset; AOF records writes under configured persistence/fsync behavior. Choose a recovery-point target, storage budget, and tested restore procedure. Snapshot/fork and disk work can affect latency and memory; persistence is a separate concern from whether clients receive fast acknowledgements. Managed products can expose different controls. [Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/).

## Latency, security, and operations

Inspect command latency, client/pool waits, network round trips, large keys, memory/evictions, slow commands, persistence work, and replication lag. Pipelining reduces round trips; it does not make the batch a transaction. Prefer bounded incremental iteration over blocking full-keyspace scans for large deployments.

Restrict network reachability, use supported authentication/ACLs and transport encryption, and scope key access where available. Separate workloads with conflicting eviction, durability, or resource needs. Monitor queue state independently of cache hit rate.

## Interview drills

- Explain why Redis can use threads while ordinary command execution is mostly serialized.
- Distinguish one atomic command, a pipeline, MULTI/EXEC, WATCH, and a script.
- Explain TTL expiry versus memory eviction versus application invalidation.
- Diagnose why adding shards does not fix one hot key.
- Recover after a failover whose final write outcome is unknown.
- Explain why a shared Redis cache is different from a process-local Celery cache.

## References

- [Latency and threading](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/)
- [Transactions](https://redis.io/docs/latest/develop/using-commands/transactions/)
- [Data types](https://redis.io/docs/latest/develop/data-types/)
- [Pub/Sub](https://redis.io/docs/latest/develop/pubsub/)
- [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/)
- [Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)
