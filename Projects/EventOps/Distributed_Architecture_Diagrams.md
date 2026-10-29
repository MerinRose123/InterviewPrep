# EventOps — microservices, scale, and distributed-systems diagrams

[Project guide](Interview_Guide.md) · [Challenge scenarios](Project_Challenge_Scenarios.md) · [Interview Q&A](05_Interview_QA.md)

These diagrams separate the **project architecture** from **interview scenarios**. The system used Angular, Nginx, Django/Flask, Docker Compose on EC2, shared PostgreSQL, Celery/Redis, and external calendar/email integrations. The individual service boxes are **logical capabilities**, not a claim that every box was deployed as an independent service.

## 1. High-level architecture: what runs where?

```mermaid
flowchart TB
  U[Users] --> UI[Angular UI]
  subgraph EC2[AWS EC2 / Docker Compose]
    NX[Nginx reverse proxy]
    subgraph PY[Python backend: Django and extracted Flask services]
      EV[Events and scheduling]
      RES[Space / equipment capabilities]
      ACC[Users / authorization / tenant context]
      REP[Reporting and notifications]
    end
    BROKER[(Redis: Celery broker)]
    WORK[Celery workers]
    BEAT[Celery Beat]
  end
  UI -->|HTTP requests| NX
  NX --> EV
  NX --> RES
  NX --> ACC
  NX --> REP
  EV --> DB[(Shared PostgreSQL)]
  RES --> DB
  ACC --> DB
  REP --> DB
  REP -->|Queue work| BROKER
  BEAT -->|Schedule periodic work| BROKER
  BROKER -->|Deliver tasks| WORK
  WORK --> DB
  WORK --> S3[(Amazon S3: PDFs)]
  WORK --> MAIL[SendGrid]
  EV --> CAL[Out-of-office calendar]
```

**Explain in an interview:** Nginx routes requests to backend capabilities; it is not the application runtime. Redis carries asynchronous work, while PostgreSQL stores transactional application data. The shared database is a significant coupling point even when Python components are deployed separately. Docker Compose manages container configuration and startup; it does not guarantee application readiness or distributed high availability.

**Scale discussion:** Multiple stateless backend replicas can increase request capacity, but the database, worker throughput, external APIs, and proxy become separate bottlenecks. Scaling Celery consumers increases background concurrency, not HTTP throughput. Adding replicas requires consistent authorization and tenant handling.

## 2. Request flow versus asynchronous side effects

```mermaid
sequenceDiagram
  participant UI as Angular
  participant NX as Nginx
  participant API as EventOps backend
  participant DB as PostgreSQL
  participant Q as Redis / Celery
  participant W as Celery worker
  participant E as Email provider
  UI->>NX: Create or update event
  NX->>API: Route HTTP request
  API->>DB: Validate and persist event
  DB-->>API: Commit outcome
  API-->>UI: Event response via Nginx
  Note over API,Q: Notification dispatch is a separate side effect
  API->>Q: Enqueue notification work
  Q-->>W: Deliver task
  W->>E: Send notification
  E-->>W: Delivery API response
```

**Distributed-systems question:** What if the database commits but enqueue fails? The event exists but notification may be missing. Discuss an outbox as a hardening option. What if the email succeeds but the worker crashes before acknowledging? A retry may send twice; use a stable notification identity and delivery-state checks.

## 3. Concurrent resource reservation: read-check-write race

```mermaid
sequenceDiagram
  participant A as Request A
  participant B as Request B
  participant API as Scheduling backend
  participant DB as PostgreSQL
  A->>API: Reserve equipment 10:00–11:00
  B->>API: Reserve equipment 10:30–11:30
  API->>DB: A reads available slots
  DB-->>API: No conflict observed
  API->>DB: B reads available slots
  DB-->>API: No conflict observed
  Note over API,DB: Both reads can succeed before either write commits
  API->>DB: A commits reservation
  API->>DB: B attempts conflicting reservation
  DB-->>API: Reject conflict if DB invariant is enforced
```

**Interview design:** Enforce the no-overlap invariant at the authoritative database boundary, e.g. PostgreSQL exclusion constraints for suitable interval schemas or a serialized resource-row lock plus check. Ordinary application-level availability checks alone do not prevent races.

**Follow-ups:** Multi-resource bookings, deadlocks and lock order, retry after timeout, transaction isolation, calendar staleness, tenant scoping.

## 4. Shared database versus service-owned databases

```mermaid
flowchart LR
  subgraph CURRENT[Incremental extraction / shared data]
    S1[Scheduling capability] --> D1[(Shared PostgreSQL)]
    S2[Equipment capability] --> D1
    S3[Reporting capability] --> D1
  end
  subgraph OPTION[Alternative: independently owned data]
    T1[Scheduling service] --> D2[(Scheduling DB)]
    T2[Equipment service] --> D3[(Equipment DB)]
    T1 -.->|API or events| T2
  end
```

**Trade-off:** Shared data simplifies cross-feature queries and incremental migration but couples schema changes and can undermine service ownership. Database-per-service improves autonomy but requires explicit consistency, contract, and reporting designs. A modular monolith can also be a valid intermediate choice.

## 5. Failure and scaling drills

| Interviewer asks | What to explain |
|---|---|
| Nginx returns 502 | Route, upstream container address, process health, timeout, and logs |
| One service is slow | Trace downstream calls and database query time; bound timeouts |
| Database connection pool is exhausted | Replica count × per-instance connections; pooling and backpressure |
| Celery queue grows | Arrival rate versus worker service rate, task duration, retries, and worker concurrency |
| Two Beat schedulers run | Duplicate scheduling risk and idempotent task processing |
| Tenant data leaks across services | Consistent tenant context, authorization at each boundary, and cross-tenant tests |
| One service deploys before a schema migration | Expand/contract schema compatibility |
| Calendar API is down | Separate unknown availability from confirmed free slots; define fallback |
