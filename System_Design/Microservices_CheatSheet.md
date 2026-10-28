# Microservices Interview Cheat Sheet

[Study index](README.md) · Related: [patterns](Design_Patterns_CheatSheet.md), [REST](REST_API_Design_CheatSheet.md), [distributed systems](Distributed_Systems_CheatSheet.md).

Choose service boundaries from business ownership, change patterns, and operational constraints. More deployed services do not automatically mean better architecture.

## Contents

- [1. Microservices vs. modular monolith?](#1-microservices-vs-modular-monolith)
- [2. How do you find service boundaries?](#2-how-do-you-find-service-boundaries)
- [3. Synchronous REST/gRPC vs. asynchronous events?](#3-synchronous-restgrpc-vs-asynchronous-events)
- [4. Gateway vs. BFF vs. service mesh?](#4-gateway-vs-bff-vs-service-mesh)
- [5. Timeouts, retries, circuit breakers, bulkheads?](#5-timeouts-retries-circuit-breakers-bulkheads)
- [6. How do you handle data consistency and events?](#6-how-do-you-handle-data-consistency-and-events)
- [7. How do you evolve or extract a service safely?](#7-how-do-you-evolve-or-extract-a-service-safely)
- [8. What should a senior-level design review include?](#8-what-should-a-senior-level-design-review-include)
- [References](#references)

## 1. Microservices vs. modular monolith?

| Architecture | Prefer when | Cost |
|---|---|---|
| Modular monolith | Small team, evolving domain, shared transactional workflows | Needs enforced module boundaries; one deployment unit |
| Microservices | Independent domain ownership/deployment/scaling are valuable | Network failures, distributed data, telemetry, release and security complexity |
| Hybrid / gradual extraction | Existing platform with a specific pressure | Coexistence/routing/data migration complexity |

**Scenario:** separate an overloaded export worker from an interactive API without splitting every model into a service. The useful boundary may be execution/resource ownership first, not an arbitrary “one table per service” rule.

**Dig deeper:** if every release needs five teams deploying together, did you achieve independence? What evidence justifies extraction: load, fault isolation, team autonomy, or compliance?

## 2. How do you find service boundaries?

Group capabilities with cohesive invariants and vocabulary: billing, provisioning, identity, search projection, exports. Define data ownership, public APIs/events, failure policy, and operational owner. Avoid sharing internal ORM models as cross-service contracts.

| Boundary signal | Possible interpretation |
|---|---|
| Frequent atomic updates together | Keep in one transaction boundary if possible |
| Independent lifecycle/scale/security | Candidate for separation |
| Many chatty synchronous calls | Boundary may be too fine-grained |
| Same data written by several teams | Ownership is unclear; extraction may worsen it |

**Dig deeper:** a separate DB per service can mean logical ownership rather than a separate physical server, but permissions and schema coupling matter. Reporting needs do not justify every service writing every table.

## 3. Synchronous REST/gRPC vs. asynchronous events?

| Choice | Fit | Tradeoff |
|---|---|---|
| REST/HTTP | Immediate request/response, broad interoperability | Caller depends on downstream latency/availability |
| gRPC | Typed contracts and efficient internal RPC/streaming | Client/runtime/proxy and compatibility considerations |
| Event/message | Decoupled processing and fan-out/replay | Eventual consistency, duplicates, schema ownership |
| Batch/object exchange | Large data artifacts | Higher latency; manifest/version/recovery design |

**Scenario:** checkout needs an immediate authoritative stock decision; analytics can consume an event later. Do not make a user request synchronously wait on nonessential email/report generation.

**Dig deeper:** timeout does not imply remote rollback. How do you propagate deadlines, cancellation, operation identity, and trace context? What is the maximum fan-out and retry amplification?

## 4. Gateway vs. BFF vs. service mesh?

| Component | Role | Limit |
|---|---|---|
| API gateway | External routing, authentication integration, quotas | Does not replace domain/object authorization |
| BFF | Client-specific aggregation and browser session/token boundary | Extra API ownership and duplication risk |
| Service mesh | Selected transport policy/telemetry/mTLS infrastructure | Operational cost; cannot fix poor domain boundaries |
| Reverse proxy | Route/terminate/buffer connections | Timeouts/body limits/headers need configuration |

**Dig deeper:** avoid turning the gateway into a centralized business-logic bottleneck. Who owns compatibility? How do long-lived connections drain during rollout?

## 5. Timeouts, retries, circuit breakers, bulkheads?

```text
Caller deadline 2 s:
  bounded queue wait + connection acquisition + attempt(s) + response work <= budget
Retry only classified transient failures within remaining deadline.
Use stable operation identity for retryable side effects.
```

| Mechanism | Solves | Trap |
|---|---|---|
| Timeout | Bounds waiting | Underlying work may still run |
| Retry/backoff/jitter | Transient failure | Duplicate effects and synchronized load |
| Circuit breaker | Repeated calls into failing dependency | Recovery probes and threshold behavior need tuning |
| Bulkhead | Isolate resource usage | Queues still need bounds |
| Rate limiter | Bound admission over time | Not identical to in-flight concurrency control |

**Dig deeper:** which layer retries? If a DB is saturated, more replicas/retries can worsen it. Does a fallback return stale but acceptable data or fabricate financial success?

## 6. How do you handle data consistency and events?

Own mutations in one service. Prefer a local transaction where the invariant fits; publish durable intents using an outbox. Consumers use inbox/deduplication where needed. A DB commit plus broker publish in ordinary application code is not automatically atomic.

| Pattern | When useful | Cost |
|---|---|---|
| Saga | Multi-service business steps | Intermediate states, compensation/reconciliation |
| CQRS | Different read/write models genuinely needed | Projection lag and extra data ownership |
| Event sourcing | Event history is the authoritative state model | Schema evolution, replay, snapshots, privacy complexity |
| CRUD + audit log | Ordinary state management with audit needs | Audit completeness and transactional capture |

CQRS does not require event sourcing; event-driven architecture does not automatically mean event sourcing. See [distributed systems](Distributed_Systems_CheatSheet.md) for Saga/2PC.

**Dig deeper:** a projection can lag after a successful write. What does the user see? What happens if a replay repeats external notifications?

## 7. How do you evolve or extract a service safely?

Strangler approach: introduce a controlled routing seam → extract one capability → establish one authoritative writer → backfill/verify data → switch traffic gradually → retire old path. Avoid indefinite dual writes without a recovery/ordering strategy.

Use versioned contracts, tolerant readers where safe, migration windows, and compatibility tests. Roll out additive schema changes before consumers depend on them; remove old behavior only after usage evidence supports it.

**Dig deeper:** can you roll back routing after new writes exist? Is the old service able to read the new schema? How do you reconcile divergence during migration?

## 8. What should a senior-level design review include?

Define availability/latency goals, owner/on-call, capacity limits, tenant isolation, secrets, dependencies, deployment strategy, failure drills, and cost. Trace a request and an event through the full system. Use distributed tracing and operation status rather than asking operators to correlate unstructured logs manually.

**Resume drill:** describe how Docker/Nginx/Celery/Redis fit together in your actual system. Explain which parts were independently deployable and how you tested inter-service integration, rather than equating containerization alone with microservices.

## References

- [Azure microservices architecture guidance](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/microservices)
- [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)
- [Azure CQRS pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs)
- [Azure strangler pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig)
