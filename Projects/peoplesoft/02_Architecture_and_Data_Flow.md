# peoplesoft — Architecture and data flow

[Cloud Manager guide](Cloud_Manager_Interview_Guide.md) · [PeopleSoft runtime architecture](PeopleSoft_Architecture_and_Distributed_Systems.md) · [Challenge scenarios](03_Engineering_Challenges.md)

**Key distinction:** Cloud Manager is an infrastructure-orchestration product. The managed PeopleSoft runtime contains web, application, batch, database, and search components. Do not present Cloud Manager itself as a conventional independently deployed microservices platform.

## 1. Control plane versus managed environment

```mermaid
flowchart TB
  ADMIN[Administrator / lifecycle request] --> CMUI[Cloud Manager UI / REST entry]
  subgraph CONTROL[Cloud Manager orchestration control plane]
    CMUI --> JOB[Lifecycle workflow / job tracking]
    JOB <--> STATE[(Operation / configuration state)]
    JOB --> AUTO[Python / Java / scripts / Terraform / OpenTofu]
  end
  AUTO --> OCI[OCI APIs: compute / network / storage / DB]
  AUTO --> VAULT[OCI Vault]
  AUTO --> ART[Images / patches / deployment artifacts]
  AUTO -->|Remote configuration| TARGET
  subgraph TARGET[Managed PeopleSoft environment]
    LB[Web entry / load balancing]
    WEB[WebLogic / PIA web tier]
    APP[Tuxedo application domains]
    BATCH[Process Scheduler / batch]
    DB[(Oracle Database / Exadata option)]
    SEARCH[OpenSearch cluster]
    LB --> WEB
    WEB --> APP
    APP --> DB
    BATCH --> DB
    APP --> SEARCH
  end
  TARGET -.->|Operation results / status| JOB
```

**Interview narrative:** Cloud Manager coordinates resources and lifecycle actions; PeopleSoft handles business traffic after deployment. Control-plane success does not prove application readiness. The OCI API, target VM, domain processes, database, and job state can temporarily disagree.

**Scale discussion:** Scaling Cloud Manager's orchestration throughput is different from scaling PeopleSoft web/app nodes, Process Scheduler capacity, Oracle Database, or OpenSearch shards. Identify the bottleneck and the independently scalable component before choosing a remedy.

## 2. Provisioning workflow with partial-failure recovery

```mermaid
sequenceDiagram
  participant U as Administrator
  participant C as Cloud Manager
  participant S as Operation state
  participant O as OCI
  participant T as Target VM
  participant P as PeopleSoft runtime
  U->>C: Provision environment
  C->>S: Record lifecycle operation
  C->>O: Create infrastructure
  alt OCI response received
    O-->>C: Resource ID / operation state
  else Response times out
    C->>S: Mark outcome unknown
    C->>O: Reconcile by operation/resource identity
    O-->>C: Observed infrastructure state
  end
  C->>T: Configure OS and software
  T-->>C: Bootstrap result
  C->>P: Validate DB, application, batch, search
  P-->>C: Readiness result
  C->>S: Record final phase and status
  C-->>U: Display outcome
```

**Design discussion:** This is a recovery-oriented model of a lifecycle workflow. A timeout is not proof of failure. Retrying a create operation without checking the provider may duplicate resources. Job checkpoints and resource ownership support recovery and safe cleanup.

## 3. Concurrent environment operations and stale workers

```mermaid
sequenceDiagram
  participant A as Operator A
  participant B as Operator B
  participant C as Lifecycle controller
  participant S as Durable environment state
  A->>C: Start clone
  C->>S: Acquire environment operation ownership
  S-->>C: Clone accepted
  B->>C: Start patch on same environment
  C->>S: Check conflicting operation
  S-->>C: Clone already active
  C-->>B: Reject / defer patch
  Note over C,S: After crash, resume using durable phase and ownership
```

**Trade-offs:** Serializing incompatible operations protects environment consistency but limits concurrency for that environment. Operations on independent environments can still run concurrently. Terraform state locking protects IaC state; it does not automatically serialize every credential rotation, application patch, and cloud lifecycle job.

## 4. Managed PeopleSoft runtime: synchronous versus asynchronous

```mermaid
flowchart LR
  B[Browser] -->|HTTPS| W[WebLogic / PIA]
  W -->|Jolt request| A[Tuxedo application server]
  A -->|SQL| DB[(Oracle Database)]
  A -->|Submit process request| PR[(Process request tables)]
  PR -->|Polled| S[Process Scheduler]
  S -->|Execute| BATCH[Application Engine / COBOL / SQR]
  BATCH --> DB
  EXT[External systems] <-->|Integration Broker| IB[IB gateway / engines]
  IB <--> DB
  A -->|Search queries| OS[OpenSearch]
```

**Explain:** Browser business requests, asynchronous Process Scheduler work, and Integration Broker message flows have different execution and delivery semantics. Tuxedo queues are not interchangeable with Kafka, Celery, or a cloud message broker. Search indexing is a separate consistency path from transactional SQL.

## 5. Search cluster expansion versus reindexing

```mermaid
flowchart LR
  DB[(Application data)] --> INDEX[Search Framework extraction / indexing]
  INDEX --> SHARDS[(OpenSearch primary and replica shards)]
  NODE[Add compatible data node] --> ALLOC[Shard allocation / rebalance]
  SHARDS --> ALLOC
  ALLOC --> QUERY[Search query capacity and resilience]
  REINDEX[Reindex operation] -->|Rebuild documents| SHARDS
```

**Trade-off:** Adding nodes can redistribute shards and capacity; reindexing rebuilds documents. A healthy cluster does not imply fresh search results. Query throughput, indexing rate, shard counts, disk watermarks, and network costs may limit gains from more nodes.

## 6. Credential rotation during scaling

```mermaid
sequenceDiagram
  participant C as Cloud Manager
  participant V as OCI Vault
  participant N as New application node
  participant D as Dependent service / DB
  C->>V: Retrieve authorized credential
  V-->>C: Secret version / value
  C->>N: Configure node with credential
  N->>D: Validate fresh connection
  D-->>N: Authentication outcome
  N-->>C: Node readiness result
  Note over C,D: Rotation and scale operations must coordinate credential generation
```

**Failure discussion:** A node configured with a stale password may bootstrap successfully yet fail application readiness. Vault access control, secret rotation, consumer update, and validation are distinct responsibilities.

## 7. Distributed-systems interview drills

| Question | Answer direction |
|---|---|
| OCI create call times out | Unknown outcome, provider reconciliation, stable operation identity |
| VM exists but bootstrap fails | Phase checkpoints, safe retry, ownership-aware cleanup |
| Two operations target one environment | Durable operation coordination and conflict policy |
| A stale worker resumes | Fencing / ownership generation and state validation |
| App reports healthy but DB is unreachable | Layered readiness checks, not just process status |
| New search node does not help | Shard distribution, query/indexing bottleneck, disk/network limits |
| Search result is stale after SQL commit | Separate indexing pipeline and eventual consistency |
| Credential rotates during node creation | Coordinate versions and validate fresh connections |
| Terraform state is locked | IaC serialization, not universal lifecycle serialization |
| Customer count is high | Measure actual concurrency, latency, duration, and failure rate |
