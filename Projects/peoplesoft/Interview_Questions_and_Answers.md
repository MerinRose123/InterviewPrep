# PeopleSoft: interview questions and answers

**50 practice questions | Cloud Manager, architecture, and distributed systems**

Use this file for spoken practice. Start with a direct answer, then add a concrete mechanism, a failure case, and your actual contribution. Personal implementation details and measurements must match your experience; proposed designs are not claims about delivered product internals.

The answers are collected from the two researched guides. Follow their references and diagrams for deeper study:

- [Cloud Manager project and orchestration guide](Cloud_Manager_Interview_Guide.md)
- [PeopleSoft architecture and distributed mechanisms](PeopleSoft_Architecture_and_Distributed_Systems.md)
- [Terraform execution and state guide, including 12 additional interview answers](Terraform_Interview_Guide.md)
- [OCI Vault master keys, security, and credential rotation](Cloud_Manager_Interview_Guide.md#how-oci-vault-protects-credentials)
- [Technology comparisons with familiar backend and cloud stacks](Technology_Comparisons.md)
- [Real debugging stories: CM 16 OCI CLI dependency failure](Debugging_Stories.md)

## Practice order

1. Architecture overview: questions 21–28.
2. Messaging and background work: questions 29–34.
3. Search and analytics: questions 10–12 and 35–41.
4. Database, RAC, and Exadata: questions 13–14 and 42–44.
5. Cloud orchestration, credentials, and recovery: questions 1–9 and 15–20.
6. Distributed failures and personal ownership: questions 45–50.

## Part A: Cloud Manager and orchestration

### 1. Why call Cloud Manager distributed?

One operation coordinates independently executing components across network and process boundaries. OCI state, VM state, deployment state, database readiness, and stored job status can disagree temporarily. Timeouts, partial completion, retries, and reconciliation are central problems.

### 2. Is it a microservices platform?

It is an infrastructure orchestration product with distributed interactions. My Python/Java and REST experience does not alone establish independent microservice deployment or database ownership. I would describe the actual service/process boundaries of the component I worked on.

### 3. How do services communicate?

Separate the boundary: Cloud Manager documents internal IB REST services for asynchronous activity results; OCI operations use the appropriate cloud APIs/tooling; Linux and Windows management can involve SSH and HTTPS WinRM; managed PeopleSoft runtime uses Jolt/Tuxedo, database connections, and Integration Broker. There is no single transport for all interactions.

### 4. What makes an operation asynchronous?

Its execution outlives the submitting request. A later status observation or callback communicates progress. Individual transport calls can still be synchronous. Acceptance is different from successful infrastructure creation and from validated application readiness.

### 5. How do you guarantee exactly-once provisioning?

I would avoid promising global exactly-once execution. Use stable operation identity, safe provider retry behavior, durable phase tracking, idempotent steps where possible, and reconciliation. A timeout can hide successful creation; blindly replaying the create call can leak resources.

### 6. Where is the message queue?

First clarify which workload. Tuxedo IPC queues dispatch local services; Integration Broker has durable asynchronous runtime state; Process Scheduler polls database-backed requests. Cloud Manager’s public callback documentation does not establish Kafka, RabbitMQ, Celery, or one specific internal orchestration queue.

### 7. What happens when a callback is lost?

The controller should inspect operation progress and actual resource state, using a timeout and reconciliation policy. Re-executing a non-idempotent action solely because its callback is absent is unsafe. In a real project answer, name the implemented recovery mechanism rather than only describing the ideal.

### 8. How do you recover a failed workflow?

Identify the last verified phase and distinguish recoverable prerequisites from invalid configuration or irreversible changes. Resume safely completed work when supported; compensate only owned resources where appropriate. Preserve diagnostic context and validate the final state.

### 9. Is rollback just the reverse of provisioning?

No. Some resources are shared or imported; some steps create external side effects; database upgrades can be incompatible with old software. Recovery may require restore, forward repair, or controlled compensation rather than reversing every command.

### 10. Why is search eventually consistent?

The transactional database and the search index are separate stores. Extraction, transfer, indexing, refresh, and retries add delay. A successful business commit does not establish that a subsequent search sees the change immediately.

### 11. Why do you need Logstash if you already have PeopleSoft indexing?

They serve different paths. Search Framework can build application indexes through Application Engine and Direct Transfer/IB mechanisms. Logstash supports configured ingestion such as external data and PeopleSoft Health Center. It is not mandatory in every application transaction or index build.

### 12. What is the difference between node clustering and reindexing?

Clustering coordinates search nodes and shard placement. Reindexing creates or rebuilds searchable data. A healthy cluster can contain stale or empty indexes; a completed extraction can still leave failed shard writes or incorrect access controls.

**Add-node follow-up:** adding a compatible data node to the same cluster normally uses shard allocation/rebalancing, not a full rebuild from the application database. Your confirmed contribution was the add-node functionality; the exact remembered reindexing step remains unverified. See the [recommended workflow and evidence checklist](Cloud_Manager_Interview_Guide.md#adding-a-node-recommended-approach-and-the-reindexing-distinction).

### 13. Why Exadata rather than an ordinary DB VM?

Exadata is an Oracle database platform with specialized infrastructure and service capabilities. The choice depends on workload, availability, consolidation, operational requirements, and cost. It does not automatically fix bad SQL, application locks, or inefficient batch processing.

### 14. Is RAC equivalent to sharding?

No. RAC instances access a shared database. OpenSearch shards partition index data. These have different storage, coordination, and failure models. Do not draw RAC nodes as independent databases unless describing separate databases intentionally.

### 15. How do you rotate credentials without breaking scaling?

Coordinate the two operations or validate credential generation before activating the new node. Update the credential authority and consumers using a target-specific sequence, then test fresh connections. Explain overlap or downtime only when supported by the authentication system.

### 16. Why can a job say successful while the application fails?

The job may have checked only a lower layer: API acceptance, VM state, or process startup. A useful readiness gate exercises dependent services and a representative workload. Describe what the actual product checked and what improvement you made.

### 17. How do you prevent concurrent conflicting operations?

Define permitted combinations and serialize incompatible environment mutations. Combine durable ownership with stale-worker protection where needed. Infrastructure state locking alone does not protect a simultaneous secret rotation or application upgrade.

### 18. How did you validate your change?

Use an actual feature example: supported topology/release combinations, success path, partial failure, retry/resume, compatibility, security, and cleanup. Distinguish checks you performed personally from the broader QA/release process.

### 19. Does serving 2,000 customers prove scalability?

It establishes adoption context if accurate. Scalability requires workload measurements: operation concurrency, environment size, duration, failure rates, resource limits, and bottlenecks. I would give actual measured data when available rather than converting customer count into throughput.

### 20. What would you improve?

Choose a defensible proposal: clearer phase readiness, operation correlation, fewer manual recovery steps, stronger reconciliation, safer credential convergence, or better failure injection. Explicitly label it as a proposed improvement if you did not implement it.

## Part B: PeopleSoft architecture and distributed mechanisms

### 21. Draw the architecture and explain why it is distributed.

Draw browser, web, application domain, database, scheduler, IB gateway/engine, search, and dashboards/ingestion. Label HTTPS, Jolt, local IPC, SQL, integration HTTP(S), and search transfer. Explain independent execution and partial failure. Then add Cloud Manager outside the business request path as lifecycle orchestration.

### 22. What is the difference between WebLogic and Tuxedo here?

WebLogic hosts PeopleSoft’s web application and gateway components. Tuxedo manages application-domain services and runtime facilities. PeopleSoft application processes execute the business logic and database calls. Both participate, but at different layers.

### 23. What does Jolt do?

It provides the Java-side interface to Tuxedo services used by the web-tier software. Listener/handler processes establish and handle these connections. It is not the browser’s HTTP protocol, a relational database protocol, or Integration Broker’s durable message store.

### 24. How do application processes communicate on the same host?

Tuxedo uses local OS IPC facilities, including request/reply message queues and shared-memory runtime information such as the bulletin board. Network communication between machines is a different boundary. Local IPC does not imply a durable externally replayable event log.

### 25. Does each user get one PSAPPSRV and one DB connection?

No. Worker processes service requests and maintain their own relevant connections. Browser sessions and application processes have different lifetimes. Actual pool/session configuration and stateful behaviors matter, but one logged-in user is not automatically one dedicated process.

### 26. What is stored in the bulletin board?

Runtime configuration and service information used by Tuxedo processes. BBL coordinates local administrative/runtime information. It is not the PeopleSoft business database or the persistent history of asynchronous integrations.

### 27. Is a Tuxedo service the same as an IB service operation?

No. A Tuxedo service is an advertised runtime service handled by a server process. An IB service operation is an application integration contract with messages, handlers, routing, and processing semantics. IB runs using application-server facilities but exposes a different abstraction.

### 28. How does an external application call PeopleSoft?

For an IB integration, it calls an appropriate gateway listening connector over the configured protocol. The gateway connects to the application-side engine; routing and handlers determine processing. The response or asynchronous acknowledgment depends on the service operation. Not every external integration is the same URL or authentication mode.

### 29. How does asynchronous messaging survive a worker failure?

IB maintains durable runtime state separately from handler process memory. Recovery uses the recorded processing state and supported retry/monitoring behavior. Exactly which items resume or require intervention depends on status, operation configuration, and the failure point. Avoid promising automatic replay of every external business side effect.

### 30. Why can one failed message block other messages?

An ordered queue preserves dependencies. A failed earlier item can block later items in its applicable ordering scope. Diagnose the first failure, queue partition, and target node. Unordered processing improves parallelism only when the business logic can tolerate it.

### 31. Where do background tasks run?

Scheduled batch commonly runs through the separate Process Scheduler facility, launched from database-backed requests. Integration handlers, search indexing, and cloud lifecycle jobs have their own execution paths. “Background” describes timing relative to the caller, not one universal worker framework.

### 32. Is Application Engine always asynchronous?

No. Batch execution through Process Scheduler is separate from online synchronous `CallAppEngine` invocation. The invocation mechanism determines whether the caller waits and what transaction rules apply.

### 33. Why can a successful process have no report?

Execution and distribution are separate phases. Check whether the output was generated, then the Distribution Agent, repository endpoint, permissions, and transfer status. Rerunning the business program can duplicate effects without repairing the distribution problem.

### 34. What happens if a batch fails halfway through?

Earlier commits can remain. With appropriate checkpoint/restart design, it resumes from a supported boundary. Persistent state and business-row logic matter. External effects need additional handling because a checkpoint does not reverse an already sent message or file transfer.

### 35. How does PeopleSoft data reach OpenSearch?

Search Framework selects and extracts data according to search definitions, often through scheduled Application Engine builds. Full Direct Transfer can send it directly; configured non-Full-Direct-Transfer paths can involve IB. Real-time indexing has its own change-capture/staging flow. Logstash is not a universal mandatory hop.

### 36. What do Kibana and OpenSearch Dashboards do?

They visualize/query data indexed in their respective compatible search stacks. PeopleSoft integrates these capabilities for analytics/Insights and monitoring use cases. They do not store the authoritative relational business transaction data.

### 37. What does Logstash do?

It ingests, transforms, and outputs configured events/data. PeopleSoft documents external-data and Health Center uses. The actual pipeline must be named; the fact that Logstash exists does not establish that all application logs or business transactions flow through it.

### 38. Why can a saved record be missing from search?

The record may not satisfy the search definition or security filter, or indexing may be delayed/failed. Check definition scope, build/RTI status, transfer errors, target index, and user authorization. Database commit and index visibility are separate events.

### 39. What is the difference between shards and replicas?

Primary shards partition unique index data; replicas copy those partitions. Replicas improve availability and can add search-serving capacity, while increasing storage and replication work. Additional nodes do not automatically fix poor shard design.

### 40. Why use three search nodes?

Oracle recommends a three-node cluster on separate physical servers in the referenced guidance. Availability depends on data-copy placement and coordination, plus sufficient remaining capacity. Three VMs do not prove three independent failure domains or any specific dedicated-role layout.

### 41. Does green search-cluster health prove the application is healthy?

No. Green indicates shard allocation. The index can be empty, stale, incorrectly secured, or slow, and PeopleSoft can have bad endpoint credentials. Validate application queries and user-specific visibility separately.

### 42. What is Exadata versus Oracle Database?

Oracle Database is the DBMS. Exadata is a platform for running it with engineered infrastructure. PeopleSoft connects to database services; application middleware and business logic remain separate components.

### 43. How is RAC different from OpenSearch clustering?

RAC coordinates multiple instances over a shared database. OpenSearch distributes partitioned index shards and replicas across nodes. Both involve distributed coordination, but their data placement, transaction semantics, and recovery models differ substantially.

### 44. Why is RAC insufficient for disaster recovery?

It protects against certain compute/node failures within its architecture. A separate standby through Data Guard and tested application/site recovery address other failures. Logical mistakes and recovery history also require backup/retention strategy.

### 45. Can adding application servers reduce performance?

Yes. Extra workers can create more database sessions, lock contention, memory pressure, or simultaneous search/indexing work. Measure bottlenecks and downstream capacity rather than assuming linear scaling.

### 46. What happens during a network partition?

Specify which link failed. Web-to-app failure affects interactive requests; app-to-DB failure affects SQL work; search-node partition affects coordination/allocation; remote integration failure affects contracts. Different components can remain healthy locally while end-to-end work fails. Recovery must handle uncertain in-flight outcomes.

### 47. Does the whole environment use one distributed transaction?

No general claim is justified. Oracle DB transactions have defined scope. External integrations, search writes, report distribution, and OCI operations have independent boundaries. Tuxedo transaction support does not prove every resource participates in a common XA transaction.

### 48. What does Cloud Manager add to this architecture?

It automates resource provisioning and environment lifecycle/configuration. It coordinates with cloud services and target components, so it has its own asynchronous job and recovery concerns. It is not a mandatory hop for every managed business request.

### 49. Which parts did you personally build?

“My stated scope includes Cloud Manager backend/lifecycle automation, OpenSearch add-node functionality, Exadata integration, Vault credential management, CI/CD, and infrastructure tooling. For OpenSearch, I worked on adding an additional node. I recall an indexing step but would verify its exact mechanism. The underlying PeopleTools/Tuxedo/Oracle DB mechanisms were platform dependencies I integrated with.” Add the specific modules and decisions you personally owned.

### 50. How would you explain eventual consistency with a concrete incident?

Use a real record or job: business commit succeeds, indexing or remote delivery lags, a user sees stale search or downstream state, monitoring identifies the delayed phase, and supported recovery catches up without duplicating the business transaction. If you have no real incident, explicitly present it as a hypothetical diagnostic exercise.

## Evidence and deeper references

The [Cloud Manager guide](Cloud_Manager_Interview_Guide.md#1-study-plan-and-evidence) distinguishes your documented experience from public product behavior and recommended design patterns. Its [source map](Cloud_Manager_Interview_Guide.md#14-practice-exercises-and-sources) and the [architecture guide references](PeopleSoft_Architecture_and_Distributed_Systems.md#14-study-exercises-glossary-and-research-references) link Oracle and OpenSearch documentation.

Before interviews, supply actual versions, component names, node roles/counts, retry and recovery mechanisms, validation evidence, and metric definitions. Do not infer throughput from the stated customer count or claim ownership of underlying Oracle/Tuxedo internals when your work was integration.
