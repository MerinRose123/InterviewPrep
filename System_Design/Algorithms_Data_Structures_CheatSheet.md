# System Design Algorithms and Data Structures Cheat Sheet

[Study index](README.md) · Related: [DSA](../DSA_CheatSheet.md), [caching](Caching_Performance_CheatSheet.md), [distributed systems](Distributed_Systems_CheatSheet.md).

These are engineering choices with error, memory, and migration costs. Educational implementations below are not production routing/cryptography libraries.

## Contents

- [1. Why consistent hashing instead of hash(key) % nodes?](#1-why-consistent-hashing-instead-of-hashkey--nodes)
- [2. How does a Bloom filter work?](#2-how-does-a-bloom-filter-work)
- [3. Bloom vs. counting Bloom vs. Cuckoo filter?](#3-bloom-vs-counting-bloom-vs-cuckoo-filter)
- [4. HyperLogLog: how do you count millions of unique users cheaply?](#4-hyperloglog-how-do-you-count-millions-of-unique-users-cheaply)
- [5. Count-Min Sketch and top-K?](#5-count-min-sketch-and-top-k)
- [6. What is a Merkle tree?](#6-what-is-a-merkle-tree)
- [7. Token bucket vs. leaky bucket vs. windows?](#7-token-bucket-vs-leaky-bucket-vs-windows)
- [8. LRU vs. LFU and distributed identifiers?](#8-lru-vs-lfu-and-distributed-identifiers)
- [References](#references)

## 1. Why consistent hashing instead of hash(key) % nodes?

Modulo placement changes many assignments when the node count changes. A consistent-hash ring places node positions and keys in the same hash space; a key belongs to its next clockwise node. Adding a node moves the keys in the ranges it takes over, rather than broadly remapping the key space.

```text
Ring positions: A=10, B=50, C=90
key hash 35 -> B; hash 70 -> C; hash 95 -> A (wrap)
Add D=30: keys in (10,30] move from B to D.
```

Virtual nodes give each physical server multiple positions to improve balance and support weighting. They do not fix a single hot key, ensure durability, or transfer data automatically.

```python
from bisect import bisect_left
from hashlib import sha256

def stable_hash(value):
    return int.from_bytes(sha256(value.encode("utf-8")).digest()[:8], "big")

def owner(key, ring):
    # ring: sorted non-empty list of (position, physical_node)
    if not ring:
        raise ValueError("empty ring")
    positions = [position for position, _ in ring]  # precompute in real code
    index = bisect_left(positions, stable_hash(key)) % len(ring)
    return ring[index][1]
```

Lookup is O(log V) with precomputed sorted positions for V virtual nodes; this explanatory code rebuilds the positions in O(V). Coordinate ring versions and migration; clients with different membership views can disagree.

| Placement | Benefit | Cost |
|---|---|---|
| Modulo | Simple O(1) routing | Broad remapping on membership changes |
| Ring + virtual nodes | Limited movement, weighted capacity | Ring metadata, imbalance, migration complexity |
| Rendezvous hashing | Pick node with highest key/node score; simple membership semantics | Basic lookup O(number of nodes); weighted variants need care |
| Directory/slot mapping | Explicit placement control | Reliable routing metadata and cutover protocol |

**Dig deeper:** choose replicas on distinct physical failure domains, not merely adjacent virtual nodes on the same machine. Redis Cluster's slots differ from a classic ring. How do you avoid losing writes during ownership transfer?

## 2. How does a Bloom filter work?

A bit array with k hash-derived positions: insert sets those bits; lookup tests them. A zero means absent from the filter's inserted set; all ones means possibly present. Standard Bloom filters have false positives but no algorithmic false negatives under correct insert/query operation without unsafe deletion or missing updates.

```text
Request key -> filter says absent -> skip expensive lookup only if filter is current/complete
            -> filter says maybe  -> verify in authoritative store
```

For n expected elements and target false-positive rate p:

```text
m ≈ -n * ln(p) / (ln(2)^2) bits
k ≈ (m/n) * ln(2)
Example: n=1,000,000, p=0.01 -> about 9.6 million bits (~1.2 MB), k≈7.
```

Insert/query O(k); storage O(m). Overfilling increases false positives. A stale filter missing newly inserted DB keys can produce operational false negatives relative to the DB even though the data structure is functioning correctly.

```redis
# Requires a deployment supporting these probabilistic commands.
BF.RESERVE known-products 0.01 1000000
BF.ADD known-products product:42
BF.EXISTS known-products product:42
```

**Dig deeper:** never use a Bloom “maybe” as proof that a payment/event was processed. Rebuilds need a concurrent-write catch-up strategy. [Redis Bloom reference](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/).

## 3. Bloom vs. counting Bloom vs. Cuckoo filter?

| Structure | Deletion | Strength | Cost / failure |
|---|---|---|---|
| Bloom | No safe ordinary bit clearing | Simple, compact membership filter | Clearing shared bits creates false negatives |
| Counting Bloom | Decrement counters under correct multiplicity rules | Supports removal | More memory; overflow/incorrect deletion breaks guarantees |
| Cuckoo filter | Fingerprint-based deletion when membership assumptions hold | Space-efficient approximate membership with deletion | Insertion can fail near capacity; deleting absent items can corrupt semantics |
| Exact set | Exact membership | Correctness-critical deduplication | Stores actual identities; memory growth |

**Dig deeper:** is your item ever deleted? Are duplicate insertions counted? Is “not present” safe to return during rebuild? Prefer exact DB uniqueness for business deduplication.

## 4. HyperLogLog: how do you count millions of unique users cheaply?

HLL estimates cardinality using hash-derived register statistics. It supports merging compatible sketches but does not list users or answer exact membership. Error is statistical, not a per-answer absolute guarantee.

```redis
PFADD visitors:day:2026-10-27 user:1 user:2 user:1
PFCOUNT visitors:day:2026-10-27
```

**Tradeoff:** exact sets support membership/deletion at much larger storage cost; HLL suits analytics where approximation is acceptable. Do not sum daily unique counts to compute monthly uniques; merge compatible sketches. [HLL reference](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/).

**Dig deeper:** how do time windows expire? Can you remove one user's historical contributions? Standard HLL does not provide arbitrary deletion.

## 5. Count-Min Sketch and top-K?

CMS hashes each item into one counter per row and estimates frequency using the minimum. For non-negative updates, collision interference overestimates counts under the usual assumptions. Width/depth control approximation error and failure probability; it does not enumerate all keys by itself.

| Need | Candidate | Tradeoff |
|---|---|---|
| Exact top-K from a finite stream | Size-K min-heap + exact counts where needed | O(log K) heap updates; count-map memory may dominate |
| Approximate frequencies at scale | Count-Min Sketch | Error/collisions; separate candidate tracking for top-K |
| Approximate distinct count | HLL | Not frequency or membership |

**Dig deeper:** an estimated popular IP is a signal for investigation, not automatic proof of abuse. Can independently collected sketches be merged? Only with compatible parameters/hash definitions and meaningful update semantics.

## 6. What is a Merkle tree?

Leaves hash data blocks; parent hashes combine children. Equal roots imply equal contents with the hash's collision-resistance assumptions and canonical representation. Descend mismatching branches to locate differences efficiently rather than exchanging all data.

**Uses:** replica anti-entropy, content-addressed storage, integrity verification. **Costs:** maintaining tree/version state and defining deterministic partitioning/serialization. A hash tree does not itself authenticate the trusted root or resolve concurrent updates.

**Dig deeper:** is tree construction over a stable snapshot? How do inserts change tree shape? Why must you distinguish ambiguous concatenations, leaf/internal encodings, and key ranges?

## 7. Token bucket vs. leaky bucket vs. windows?

| Algorithm | Behavior | Tradeoff |
|---|---|---|
| Fixed window counter | Count per time bucket | Boundary bursts can exceed intuitive rolling rate |
| Sliding log | Exact timestamps in recent window | O(request count) storage/work |
| Sliding-window counter | Approximate rolling count | Smaller state, boundary approximation |
| Token bucket | Refill tokens at rate r up to capacity b | Allows bursts up to budget; distributed atomicity required |
| Leaky bucket / paced queue | Smooth processing at chosen rate | Waiting queue requires size and deadline bounds |

```text
elapsed = max(0, now - last_refill)
tokens = min(capacity, tokens + elapsed * rate)
allow if tokens >= request_cost; then deduct request_cost
# Refill, decision, deduction, and timestamp update must be atomic per key.
```

**Dig deeper:** decide fail-open/closed by operation, separate per-user/tenant/global budgets, and use trusted identity rather than attacker-supplied keys. Distributed local buckets can exceed global limits; quantify the allowance.

## 8. LRU vs. LFU and distributed identifiers?

LRU tracks recent access; LFU tracks frequency, ideally with aging. Exact LRU can use a hash map + doubly linked list for O(1) operations, but synchronization/metadata are real costs. Scan-heavy workloads can evict valuable entries; approximate/admission policies can help.

| ID scheme | Strength | Risk |
|---|---|---|
| DB sequence | Compact ordered IDs | Central allocation; guessability; sequence gaps normal |
| Random UUID | Independent generation | Larger indexes; locality depends on type |
| Time-ordered UUID | Better temporal locality | Time/order/privacy details and implementation support |
| Snowflake-style | Timestamp + worker + sequence; decentralized allocation | Clock rollback, worker-ID collision, sequence overflow |

**Dig deeper:** unique does not mean unpredictable or authorized. A time-based ID is not proof of causal order across all services. What happens if two workers share an ID or a clock moves backward?

## References

- [Consistent hashing paper](https://doi.org/10.1145/258533.258660)
- [Bloom's original paper](https://doi.org/10.1145/362686.362692)
- [Redis Bloom](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/)
- [Redis HLL](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/)
- [Redis Count-Min Sketch](https://redis.io/docs/latest/develop/data-types/probabilistic/count-min-sketch/)
- [UUID specification](https://www.rfc-editor.org/rfc/rfc9562.html)
