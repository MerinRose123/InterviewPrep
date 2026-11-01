# Observability and Production Diagnosis Interview Cheat Sheet

[Study index](README.md) · Related: [memory profiling](Memory_Profiling_Performance.md), [cloud](../Cheatsheets/Cloud_Kubernetes.md), [messaging](../Cheatsheets/Kafka.md).

Observability helps infer internal behavior from evidence. Begin with user impact and a hypothesis; a dashboard full of numbers is not an incident explanation.

## Contents

- [1. Logs vs. metrics vs. traces vs. profiles?](#1-logs-vs-metrics-vs-traces-vs-profiles)
- [2. SLI vs. SLO vs. SLA? What should you alert on?](#2-sli-vs-slo-vs-sla-what-should-you-alert-on)
- [3. Why p50, p95, and p99 instead of average latency?](#3-why-p50-p95-and-p99-instead-of-average-latency)
- [4. Which metrics would you put on a backend dashboard?](#4-which-metrics-would-you-put-on-a-backend-dashboard)
- [5. How do you estimate capacity and load-test?](#5-how-do-you-estimate-capacity-and-load-test)
- [6. Walk through a slow-endpoint incident](#6-walk-through-a-slow-endpoint-incident)
- [7. Sampling, retention, and telemetry failures?](#7-sampling-retention-and-telemetry-failures)
- [8. How do you verify resilience and explain ownership?](#8-how-do-you-verify-resilience-and-explain-ownership)
- [References](#references)

## 1. Logs vs. metrics vs. traces vs. profiles?

| Signal | Best use | Cost / limitation |
|---|---|---|
| Logs | Individual events and decision/error context | Volume, privacy, query cost |
| Metrics | Aggregate trends and alerting | Cardinality and loss of per-request detail |
| Traces | Request path across services/queues | Sampling and context propagation |
| Profiles | CPU/allocation/blocking execution hotspots | Collection overhead and environment support |

Propagate trace context through HTTP and message metadata. Do not trust incoming baggage as authorization data or put secrets in it. [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/).

```json
{"event":"export_failed","operation_id":"e42","trace_id":"example-trace",
 "stage":"render","error_code":"INPUT_INVALID","duration_ms":235}
```

**Dig deeper:** record retry attempt vs. overall operation separately. How do logs from one Celery task connect to the originating request without leaking raw user data?

## 2. SLI vs. SLO vs. SLA? What should you alert on?

SLI is a measured indicator; SLO is a target over a window; SLA is an external agreement with stated consequences. Define which requests are eligible and what counts as good, including latency and correctness where relevant.

```text
Availability SLI = good eligible requests / total eligible requests
99.9% good out of 1,000,000 eligible requests -> budget of 1,000 bad requests
# Time-based budgets require a time-based definition; do not mix denominators.
```

Alert on user-impact/error-budget burn with appropriate fast/slow windows; use resource saturation as diagnostic or predictive signals. Every page needs an owner, action, and useful runbook.

**Dig deeper:** a 200 response with incorrect data is not truly good. Should a scheduled export have a request-latency SLO or “finished within 10 minutes” SLO? Are planned maintenance and client errors in the denominator?

## 3. Why p50, p95, and p99 instead of average latency?

Tail latency exposes the users harmed by queues, slow shards, pauses, and dependencies. Global percentiles cannot generally be obtained by averaging instance percentiles. Use aggregatable histogram buckets or another explicitly supported distribution method.

| Measurement | Interpretation | Trap |
|---|---|---|
| Average | Overall total duration/count | Hides long tails |
| p99 | Threshold met by about 99% under measurement definition | Needs sufficient samples and correct aggregation |
| Max | Worst observation | Noisy and sample-dependent |
| Queue time vs. service time | Waiting vs. work | Missing queue time can understate user latency |

**Dig deeper:** closed-loop load tests can reduce offered load when the server slows and hide overload. Fan-out to many dependencies can amplify tail latency. Time retries and full operations separately.

## 4. Which metrics would you put on a backend dashboard?

| Boundary | Signals |
|---|---|
| API | Rate, errors, latency distributions, active/in-flight requests |
| Resource | CPU, throttling, RSS/heap, GC, threads, file descriptors |
| DB | Query/transaction latency, locks, connections, acquisition wait |
| Queue | Backlog age/count, completion rate, retries, DLQ age |
| Cache | Hit ratio, source QPS, evictions, memory, refresh failures |
| Workflow | Stage duration, stuck operations, compensation failures |

Avoid user IDs, raw URLs, tokens, and arbitrary operation IDs as metric labels. Use bounded route templates, operation categories, status classes, and approved tenant tiers; individual IDs belong in appropriately protected logs/traces.

**Dig deeper:** low CPU with high latency often means waiting. Queue depth alone does not say whether the oldest job is starving. Does a high cache hit ratio hide an overloaded one-percent miss path?

## 5. How do you estimate capacity and load-test?

State assumptions: average/peak request rate, payload size, fan-out, read/write ratio, retention, concurrency, and burst duration. Little's Law gives average in-flight work `L = λW` for a stable system with consistent measurement boundaries.

```text
At 200 completed requests/s and average 0.5 s in-system time:
average in-flight ≈ 100 requests.
At 1 MB/event and 100 events/s:
raw ingress ≈ 100 MB/s before replication/compression/protocol overhead.
```

These are estimates to challenge, not production guarantees. Load-test representative data/skew, sustained load, bursts, cold caches, slow dependencies, recovery, and quota limits. Measure where throughput stops increasing while latency/queues grow.

**Dig deeper:** include DB pool and external API capacity before adding workers. A benchmark with uniform keys can miss a hot-tenant bottleneck. How does cost per successful operation change with scale?

## 6. Walk through a slow-endpoint incident

1. Confirm user symptom, scope, start time, recent changes, and SLO impact.
2. Compare healthy/affected instances, routes, tenants, regions, and versions.
3. Split request time into gateway, queue, application, DB, and remote calls using traces.
4. Check saturation and waits; profile if CPU/allocation is implicated.
5. Mitigate with rollback, traffic control, disabling an expensive path, or capacity within known limits.
6. Validate recovery and capture evidence for the durable fix.

**Dig deeper:** rollback code may not roll back an incompatible schema or external operation. Restarting everything can cause cold-cache load and lose diagnostic evidence. What is the safest reversible mitigation?

## 7. Sampling, retention, and telemetry failures?

| Choice | Benefit | Tradeoff |
|---|---|---|
| Head sampling | Cheap decision before full trace | Can miss rare slow/errors |
| Tail sampling | Retain selected outcomes after observation | Buffering, delay, infrastructure cost |
| Full capture for narrow window | Rich incident evidence | Storage/privacy/overhead |
| Structured logs with retention tiers | Useful filtering at controlled cost | Schema discipline and access management |

Application success must not depend on a synchronous telemetry backend. Bound buffers/export timeouts, observe dropped telemetry, and redact at source. Retain enough evidence to investigate delayed job failures without keeping sensitive payloads indefinitely.

## 8. How do you verify resilience and explain ownership?

Practice bounded fault injection: dependency timeout, cache loss, queue backlog, killed worker, bad rollout, expired credential. Define expected alerts, automated behavior, operator action, and recovery criteria before injecting faults.

**Resume drill:** explain a real production issue: symptom → evidence → diagnosis → mitigation → root cause → preventive change. Use actual data only; distinguish your actions from team-wide outcomes.

## References

- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/)
- [Google SRE: service level objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE workbook: SLO alerting](https://sre.google/workbook/alerting-on-slos/)
- [Prometheus histogram guidance](https://prometheus.io/docs/practices/histograms/)
