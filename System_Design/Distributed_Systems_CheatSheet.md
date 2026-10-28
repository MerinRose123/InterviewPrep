# Distributed Systems Interview Cheat Sheet

[Study index](README.md) · Related: [database](../Database_CheatSheet.md), [messaging](Messaging_Kafka_CheatSheet.md), [workflows](Workflow_Orchestration_CheatSheet.md).

Start from the business invariant and explicit failure assumptions. A timeout means “outcome unknown,” not necessarily “nothing happened.”

## Contents

- [1. What does CAP mean in a real incident?](#1-what-does-cap-mean-in-a-real-incident)
- [2. Which consistency model does the user need?](#2-which-consistency-model-does-the-user-need)
- [3. What is a quorum? Does R + W > N prove strong consistency?](#3-what-is-a-quorum-does-r--w--n-prove-strong-consistency)
- [4. How does leader election work, and why isn't a heartbeat enough?](#4-how-does-leader-election-work-and-why-isnt-a-heartbeat-enough)
- [5. What is a distributed lock, and how does fencing help?](#5-what-is-a-distributed-lock-and-how-does-fencing-help)
- [6. Distributed transaction vs. 2PC vs. Saga?](#6-distributed-transaction-vs-2pc-vs-saga)
- [7. Why are clocks, retries, and idempotency so important?](#7-why-are-clocks-retries-and-idempotency-so-important)
- [8. How would you test this design?](#8-how-would-you-test-this-design)
- [References](#references)

## 1. What does CAP mean in a real incident?

During a network partition, a distributed system cannot guarantee both linearizable consistency and availability in the formal CAP sense for every request. CAP consistency is not the same as the C in ACID. Partition tolerance is a failure condition to plan for, not something a multi-node deployment can wish away.

**Scenario:** inventory replicas cannot communicate. Rejecting/waiting on some requests can preserve a single authoritative allocation; accepting conflicting writes on both sides needs conflict resolution and may oversell.

| Requirement | Likely direction | Cost |
|---|---|---|
| Never allocate one unique seat twice | Coordinate through authoritative/quorum path | Some requests fail or wait during partitions |
| Keep accepting likes offline | Accept locally with later reconciliation | Temporary disagreement; merge semantics |
| Fast regional reads | Replicate/read locally where allowed | Explicit staleness or coordination latency |

**Dig deeper:** CAP availability has a precise meaning, not “99.99% uptime.” Normal-operation latency/consistency tradeoffs still exist when the network is healthy. Classify an operation and configuration, not a whole product with one permanent label.

## 2. Which consistency model does the user need?

| Model | Guarantee to discuss | Example |
|---|---|---|
| Linearizable | Operations behave as one copy respecting real-time order | Conditional ownership / coordination |
| Sequential | One global order consistent with each process's program order | Does not necessarily preserve real-time order |
| Causal | Cause precedes effect | Reply should not appear before its parent message |
| Eventual | Replicas converge if updates cease under stated assumptions | Catalog/search views |
| Read-your-writes | Session sees its own successful writes | Checkout confirmation |
| Monotonic reads | Session does not go backward to older state | Replica switching |

Transaction isolation is a separate axis: serializable transactions and linearizable individual operations are not interchangeable terms. Define multi-object behavior explicitly.

**Dig deeper:** how do you provide read-your-writes on a replica? Primary routing or a replay/version barrier, with a timeout/fallback. What happens when a session moves regions?

## 3. What is a quorum? Does R + W > N prove strong consistency?

For `N` replicas, a read of `R` and write to `W` overlap if `R+W>N`, assuming the same replica set. Example: N=3, R=2, W=2. The overlap alone does not ensure linearizability; concurrent writes, version selection, sloppy quorums, membership changes, and failure semantics matter.

| Configuration idea | Benefit | Tradeoff |
|---|---|---|
| Small read quorum | Lower read latency/more read availability | May observe older state |
| Larger write quorum | More acknowledged copies | Write latency/availability cost |
| Majority consensus | Ordered authoritative decisions | Minority cannot commit new decisions |

**Dig deeper:** does last-write-wins based on wall clocks lose writes? Clock skew can choose the wrong “last.” How is read repair different from committing a transaction?

## 4. How does leader election work, and why isn't a heartbeat enough?

A failure detector suspects a leader after missing heartbeats; it cannot always distinguish a crash from a slow/partitioned node. A consensus protocol elects authority under its rules and guards changes with terms/epochs and quorum agreement.

Raft separates leader election, replicated log agreement, and safety. A five-member voting group needs three for a majority, tolerating two unavailable members for progress under normal assumptions. Election does not instantly stop an old process executing external side effects. [Raft paper](https://raft.github.io/raft.pdf).

**Dig deeper:** use epochs/fencing at the resource. Can a leader serve a linearizable read without verifying its authority? What does membership reconfiguration require beyond editing a list of hosts?

## 5. What is a distributed lock, and how does fencing help?

```text
A obtains lease with fencing token 41
A pauses beyond lease expiry
B obtains lease with token 42 and writes
A resumes and attempts write with token 41
Resource rejects 41 because it has observed 42
```

A lease limits ownership time; it does not physically stop expired holders. A monotonically increasing fencing token lets the protected resource reject stale writers. Random owner tokens are useful for conditional release but do not establish monotonic fencing order.

```redis
SET refresh:catalog:42 random-owner-token NX PX 5000
```

For releasing a Redis lease, compare owner and delete atomically (for example, using a script). A separate GET then DEL can delete a new owner's lease. For correctness-critical ownership, use an appropriate coordination system and resource enforcement rather than treating this cache-refresh example as a universal lock.

| Alternative | Prefer when | Limitation |
|---|---|---|
| Unique constraint / atomic DB update | Invariant fits one database | Database boundary |
| DB row lock | Short transaction | Lock waits and connection lifetime |
| Coordination lease + fencing | Resource supports stale-owner rejection | Requires reliable token/lease protocol |
| Idempotency | Duplicate requests should have one business effect | Not a general replacement for mutual exclusion |

**Dig deeper:** GC pauses, network delays, and clock assumptions matter. What if the target storage cannot enforce a fencing token?

## 6. Distributed transaction vs. 2PC vs. Saga?

| Approach | Mechanism | Tradeoff |
|---|---|---|
| Local ACID transaction | One transaction manager/resource boundary | Simplest when possible; does not cover arbitrary remote calls |
| Two-phase commit | Prepare participants, then commit/abort decision | Prepared resources can block; coordinator recovery/availability costs |
| Saga | Series of committed local steps with compensations | Intermediate states visible; compensation may fail |
| Outbox + idempotent consumers | Atomic local state/event intent, eventual delivery | Duplicates, lag, and reconciliation remain |

**Saga example:** reserve inventory → charge payment → confirm order. If charge fails, release reservation. If confirmation fails after charge, retry/reconcile or refund according to policy. Compensation is a new business action, not time travel; a shipment or sent email cannot simply be undone.

**Dig deeper:** choreography distributes reaction logic across services; orchestration centralizes workflow decisions. How do you detect a stuck saga? Who resolves a failed refund? Where are deadlines and compensation state stored?

## 7. Why are clocks, retries, and idempotency so important?

Wall clocks can jump or drift. Use a monotonic clock for local durations; do not assume a timestamp establishes cross-machine causal order. Event/operation IDs, sequence numbers, versions, and logical clocks solve different problems.

Retries need a total deadline, retryable-error classification, jitter, and stable operation identity. If three layers each allow three total attempts, worst-case downstream attempts can reach 27. A failed TCP connection and a lost response after successful commit are different retry situations.

**Dig deeper:** when does an idempotency key expire? How does the server reject reuse with different request data? Can a duplicated external side effect be reconciled by provider operation ID?

## 8. How would you test this design?

Write invariants first: no negative stock, at most one active owner, every committed intent eventually reaches a terminal state. Inject failures after each durable boundary; pause old leaders; duplicate/reorder messages; partition replicas; restore backups. Verify invariants and recovery, not just HTTP success rates.

See [workflow orchestration](Workflow_Orchestration_CheatSheet.md) for durable progress and [database isolation](../Database_CheatSheet.md#practical-sql-scaling-and-isolation-questions) for concrete SQL races.

## References

- [Gilbert and Lynch: CAP formalization](https://doi.org/10.1145/564585.564601)
- [Raft paper](https://raft.github.io/raft.pdf)
- [etcd guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/)
- [Redis distributed-lock discussion](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
- [PostgreSQL prepared transactions](https://www.postgresql.org/docs/current/sql-prepare-transaction.html)
