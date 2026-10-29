# EventOps — scaling and failure scenarios

See [architecture](02_Architecture_and_Data_Flow.md), [challenges](03_Engineering_Challenges.md), and [Q&A](05_Interview_QA.md).

## Distributed system scenarios

- Concurrent resource bookings: enforce non-overlapping reservations using database transactions and constraints, not a separate availability check.
- Celery retry after email delivery: use stable notification identifiers and deduplicate side effects.
- Database saturation after scaling HTTP services: account for connection pool sizes, query latency, lock contention, and backpressure.
- Worker queue backlog: measure arrival rate, processing rate, retry rate, and queue age.
- Shared database migration: deploy backward-compatible schema changes before removing old fields.
- Tenant isolation in asynchronous tasks: preserve tenant context and enforce authorization at each data access.
- Nginx upstream failure: inspect routing, container readiness, connection limits, and timeouts.
- PDF report burst: isolate expensive work from interactive requests and cap worker concurrency.

## Interview discussion structure

For each scenario, identify the consistency invariant, failure boundary, retry behavior, capacity bottleneck, and measurable signals.
