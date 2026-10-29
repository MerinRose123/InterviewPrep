# Gordian — Architecture and data flow

[Project guide](Interview_Guide.md) · [Challenge scenarios](Project_Challenge_Scenarios.md) · [Interview Q&A](Interview_Questions_and_Answers.md)

Gordian was a **single-tenant Flask application**, not a collection of independent microservices. Its distributed-systems discussion centers on **web requests, Celery tasks, a Redis broker, process-local cached data, persistent analysis results, and PDF generation**.

## 1. End-to-end architecture with explicit execution boundaries

```mermaid
flowchart TB
  USER[Analyst] --> UI[Angular UI]
  UI --> NX[Nginx]
  subgraph EC2[AWS EC2 / Docker-packaged application]
    NX --> API[Flask backend]
    API --> ANALYSIS[Python analysis: Pandas / NumPy / TF-IDF]
    API -->|Submit report task| REDIS[(Redis broker)]
    REDIS --> W1[Celery worker process A]
    REDIS --> W2[Celery worker process B]
    W1 --> C1[LRU cache A: process-local]
    W2 --> C2[LRU cache B: process-local]
    W1 --> PDF1[WeasyPrint renderer]
    W2 --> PDF2[WeasyPrint renderer]
  end
  INPUT[(16 GB+ reference/reporting data)] --> ANALYSIS
  INPUT --> C1
  INPUT --> C2
  ANALYSIS --> MONGO[(MongoDB: analysis data)]
  API --> PG[(PostgreSQL: application data)]
  PDF1 --> OUT[PDF output]
  PDF2 --> OUT
```

**Most important detail:** The custom Celery base-task LRU cache is reused **within a worker process**. Two separate worker processes do not share the same Python memory. Redis transports task messages; it is not the large-dataset cache.

**Scale trade-off:** Increasing worker count can improve parallelism but also multiply memory use and cold-cache loading. For large data, throughput may fall when worker count exceeds the RAM or I/O budget.

## 2. Cache hit, cache miss, and retry behavior

```mermaid
sequenceDiagram
  participant API as Flask API
  participant Q as Redis broker
  participant W as Celery worker process
  participant C as In-process LRU cache
  participant D as Reference dataset
  participant R as WeasyPrint
  API->>Q: Queue report job with data reference
  Q-->>W: Deliver job
  W->>C: Lookup dataset/version key
  alt Cache hit
    C-->>W: Reuse prepared data
  else Cache miss
    W->>D: Load required reference data
    D-->>W: Data
    W->>C: Cache reusable data
  end
  W->>R: Render report
  R-->>W: PDF
  W-->>Q: Acknowledge according to task settings
```

**Failure discussion:** A worker can crash after rendering but before acknowledging; depending on acknowledgement and broker configuration, the task may be redelivered. Design report publication to tolerate duplicate execution. Cache contents disappear on worker restart.

## 3. Why more Celery workers can make things worse

```mermaid
flowchart LR
  Q[(Queued jobs)] --> W1[Worker A]
  Q --> W2[Worker B]
  Q --> W3[Worker C]
  DATA[(Large reference dataset)] -->|Load copy| W1
  DATA -->|Load copy| W2
  DATA -->|Load copy| W3
  W1 --> RAM[Combined RAM pressure]
  W2 --> RAM
  W3 --> RAM
  RAM --> OOM[Swap / OOM / reduced throughput]
```

**Capacity reasoning:** Approximate memory as `N × (worker baseline + per-process cached dataset + active task peak)`, plus database, OS, and other services. This is a planning model; shared memory and copy-on-write can change actual usage. Profile peak RSS/PSS and task duration before changing concurrency.

**Alternatives:** Fewer long-lived workers with high cache reuse; chunked/streaming transforms; precomputed sparse or partitioned reference artifacts; versioned datasets; separate resource-intensive queues.

## 4. Data-version consistency during report generation

```mermaid
sequenceDiagram
  participant UI as User
  participant API as Flask
  participant Q as Celery
  participant W as Worker
  participant D as Reference data
  UI->>API: Request report
  API->>Q: Enqueue report with dataset version v1
  Note over D: New reference dataset v2 is published
  Q-->>W: Deliver report job
  W->>D: Load or reuse pinned version v1
  D-->>W: Version v1
  W-->>UI: Report based on v1
```

**Trade-off:** Version pinning makes results reproducible but may require retaining older data while jobs run. Using “latest” at each step risks mixing versions. Versioned cache keys make invalidation and traceability clearer.

## 5. Failure and scale drills

| Interviewer asks | Strong answer direction |
|---|---|
| Why not scale Celery workers indefinitely? | Per-process cache duplication, memory pressure, I/O contention |
| Why not put 16 GB in a Redis task? | Queue identifiers/references, not bulk datasets |
| What happens on worker restart? | Local cache lost; cold load on next task |
| What if task runs longer than broker visibility timeout? | Redelivery and duplicate execution risk; configure and design idempotently |
| What if two workers miss the same cache key? | Independent loads across processes; per-key coordination must match scope |
| What if reference data changes? | Versioned inputs, cache keys, reproducible reports |
| What if PDF rendering crashes? | Separate report state and artifact publication; bounded retries |
| Why MongoDB rather than SQS? | Queryable analytical documents versus task delivery |
| How do you measure scaling? | Throughput, queue age, task duration, cache hit rate, peak RAM, retries |
