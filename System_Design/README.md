# System Design Interview Preparation

Practical senior-engineer revision: **17 architecture and system-design guides plus this index**. Technology-specific references live in [Cheatsheets](../Cheatsheets). Each sheet combines mechanisms, examples, tradeoffs, failure scenarios, verification, and deeper follow-up questions. Diagrams/configuration are explanatory; placeholders and example numbers must be adapted and measured before use.

## Priority track: microservices, scaling, and distributed systems

Use this track before the broader topic map when preparing for senior backend and platform interviews. Each topic has a distinct purpose; refer to the linked guide instead of memorizing repeated definitions.

| Step | Primary guide | What you should be able to defend | Project application |
|---|---|---|---|
| 1 | [Microservices](Microservices.md) | Boundaries, shared DB versus database-per-service, REST versus events, extraction | [EventOps architecture](../Projects/EventOps/02_Architecture_and_Data_Flow.md) |
| 2 | [Distributed systems](Distributed_Systems.md) | Consistency, coordination, fencing, partial failure, Saga | [Cloud Manager architecture](../Projects/PeopleSoft/02_Architecture_and_Data_Flow.md) |
| 3 | [Messaging and Kafka](../Cheatsheets/Kafka.md) | Queue semantics, ordering, duplicates, consumer groups, retries | [EventOps failure scenarios](../Projects/EventOps/04_Scaling_and_Failure_Scenarios.md) |
| 4 | [REST/API design](REST_API_Design.md) | Idempotency, concurrency, pagination, async job APIs | [EventOps challenges](../Projects/EventOps/03_Engineering_Challenges.md) |
| 5 | [Caching and performance](Caching_Performance.md) | Cache scope, invalidation, stampedes, bottleneck diagnosis | [Gordian architecture](../Projects/Gordian/02_Architecture_and_Data_Flow.md) |
| 6 | [Large-data background processing](Large_Data_Background_Processing.md) | Celery, memory limits, task retries, worker scale | [Gordian failures](../Projects/Gordian/04_Scaling_and_Failure_Scenarios.md) |
| 7 | [Workflow orchestration](Workflow_Orchestration.md) | Durable operations, timeouts, reconciliation, compensation | [Cloud Manager failures](../Projects/PeopleSoft/04_Scaling_and_Failure_Scenarios.md) |
| 8 | [Observability](Observability.md) | Latency, throughput, error rates, queue age, traces, SLOs | All three projects |

### Five questions to answer for every architecture diagram

1. Where is the authoritative state and who owns writes?
2. Which calls are synchronous, asynchronous, or eventually consistent?
3. What happens if the response is lost after the operation succeeds?
4. Which component saturates first when load increases by 10×?
5. What metric, trace, or log would prove the diagnosis?

The general guides explain mechanisms; the project guides explain how to discuss them in the context of actual engineering work.

## Topic map

| Cheatsheet | What to study |
|---|---|
| [Caching and performance](Caching_Performance.md) | Redis, cache-aside, TTL, eviction, stampede, invalidation, CDN |
| [Authentication and authorization](Authentication_Authorization.md) | Sessions/JWT, RBAC/ABAC, OAuth 2.0, OIDC, PKCE, refresh/revocation |
| [Browser storage and security](Browser_Storage_Security.md) | localStorage/sessionStorage/cookies, JWT placement, XSS, CSRF, CORS, BFF |
| [Cryptography, passwords, and secrets](Cryptography_Passwords_Secrets.md) | Hashing/encryption/signing, password storage, bcrypt/Argon2id, salts/peppers, Shamir, rotation |
| [Distributed systems](Distributed_Systems.md) | CAP, consistency, quorum, leases/fencing, leader election, 2PC, Saga |
| [Observability](Observability.md) | Logs/metrics/traces/profiles, SLOs, tail latency, capacity, incident response |
| [Memory profiling and performance](Memory_Profiling_Performance.md) | Leaks vs. churn, heap/RSS/native memory, Java/Python profiling, OOMKilled |
| [Multi-tenancy and security](Multi_Tenancy_Security.md) | Isolation, placement, noisy neighbors, IAM, network boundaries, lifecycle/audit |
| [Microservices](Microservices.md) | Boundaries, modular monolith, APIs/events, gateways, resilience, CQRS, migrations |
| [REST and API design](REST_API_Design.md) | HTTP, errors, idempotency, concurrency, pagination, async jobs, webhooks/WebSockets |
| [Algorithms and data structures](Algorithms_Data_Structures.md) | Consistent/rendezvous hashing, Bloom/Cuckoo filters, HLL/CMS, Merkle trees, rate limits, IDs |
| [Design patterns](Design_Patterns.md) | Strategy, factory/builder, adapter/decorator/proxy, observer/state, DI, distributed patterns |
| [Search systems](Search_Systems.md) | OpenSearch/Elasticsearch, mappings, shards/replicas, synchronization, live reindexing |
| [Workflow orchestration](Workflow_Orchestration.md) | Durable cloud operations, idempotency, concurrency, recovery, cancellation, versions |
| [Large data and background processing](Large_Data_Background_Processing.md) | CSV/PDF pipelines, Celery, chunking, acknowledgements, memory, fairness, recovery |
| [Infrastructure automation](Infrastructure_Automation.md) | Terraform/OpenTofu, state/locking/drift, partial applies, CI/CD, images, cost |
| [RAG and AI agents](RAG_AI_Agents.md) | Ingestion/retrieval, ACLs, tools, prompt injection, evaluation, latency/cost |

## Technology companions

Use these for tool behavior and configuration; apply them when working through the architecture guides above.

| Guide | What to study |
|---|---|
| [Messaging and Kafka](../Cheatsheets/Kafka.md) | Architecture, partitions, consumer groups, offsets, ordering, retries, DLQ, delivery semantics |
| [Cloud and Kubernetes](../Cheatsheets/Cloud_Kubernetes.md) | Object storage, containers, architecture, probes, autoscaling, networking, deployment/DR |
| [AWS networking and security](../Cheatsheets/AWS_Networking_Security.md) | Ingress/egress, security groups vs. NACLs, stateful/stateless rules, VPC routing, NAT, configuration and troubleshooting |
| [OCI vs. AWS](../Cheatsheets/OCI_vs_AWS.md) | Cloud comparison, when to choose each, service mappings, cost, availability, Oracle databases and interview answers |
| [Terraform](../Cheatsheets/Terraform.md) | Providers, execution, state, locks, drift, OCI provisioning, and recovery |
| [Technology comparisons](../Cheatsheets/Technology_Comparisons.md) | Roles, alternatives, and boundaries across backend and cloud tools |
| [MongoDB](../Cheatsheets/MongoDB.md) | Document modeling, queries, indexes, aggregation, and performance |

## Suggested study order

1. **Core API and data:** REST → authentication → browser storage → cryptography → [database design/indexing/isolation](../Cheatsheets/Database.md).
2. **Scale and failure:** caching → algorithms → messaging/Kafka → distributed systems → microservices.
3. **Production operation:** cloud/Kubernetes → AWS networking/security → observability → memory profiling → multi-tenancy/security.
4. **Resume deep dives:** workflow orchestration → large-data processing → infrastructure automation → search → RAG/agents.
5. **Design vocabulary:** patterns alongside [OOP/SOLID](../Cheatsheets/OOP.md); revisit them while explaining real projects.

## Resume-to-interview preparation map

These are practice prompts based on discussed experience, not assertions that every technique in the sheets was implemented in your projects.

| Experience to explain | Prepare to defend |
|---|---|
| Provisioning, cloning, scaling, upgrades | Durable operation state, provider timeouts, duplicate requests, ownership, recovery |
| OCI Vault credential management | Identity/permissions, rotation overlap, stale pools/workers, outage/recovery, audit |
| OpenSearch clustering/reindexing | Actual topology, visibility lag, concurrent writes/deletes, cutover/rollback |
| Celery processing of 16 GB+ CSV | Streaming/chunks, per-worker memory, cache scope, checkpoints, fairness, cancellation |
| Multi-tenant Django backend | Tenant filters across DB/cache/search/objects/jobs and test coverage |
| Terraform/CI/CD improvements | State boundaries, drift, failed applies, artifact review, measured cost impact |
| RAG/agent workflows | Evidence retrieval, ACLs, tool limits, evaluation method and actual productivity evidence |

## A repeatable system-design interview approach

1. Clarify users, operations, data relationships, invariants, and scope.
2. Define latency/availability/freshness goals and failure tolerance.
3. Estimate traffic, payloads, storage/retention, concurrency, and growth; label assumptions.
4. Sketch a simple read path and write path with explicit data ownership.
5. Explain schema/indexes, API/events, and operation identity.
6. Identify bottlenecks and compare alternatives before introducing scale mechanisms.
7. Walk through crash, timeout, duplicate, stale read, overload, and tenant-leak scenarios.
8. Cover deployment, monitoring, recovery, security, cost, and tests.

For each answer: **mechanism → example → tradeoff → failure → evidence**. Use measured project numbers only when known; customer count is not request throughput. Distinguish your implementation experience from techniques you have studied.

## Practice designs

| Exercise | Main sheets | Failure to walk through |
|---|---|---|
| [Idempotent order creation (pseudocode)](REST_API_Design.md#interview-example-create-an-order-safely-on-retry) | REST, database transactions | Order commits but the response is lost; client retries |
| Tenant-aware export service | REST, background processing, memory, security | Worker dies after upload but before checkpoint |
| Cloud environment orchestrator | Workflows, infrastructure, distributed systems | Resource created but provider response lost |
| Search platform migration | Search, messaging, observability | Update/delete races during reindex |
| Login and credential platform | Auth, browser, cryptography | Token theft, refresh race, signing/secret rotation |
| Event-driven order workflow | Messaging, microservices, Saga | Payment succeeds while order confirmation fails |
| Debugging assistant | RAG, search, security | Malicious log content asks tool to reveal a secret |

## Example and source conventions

Source links point to primary documentation/specifications or original research. Rolling documentation may describe a newer version than your deployment; check the project's pinned versions. Snippets with application collaborators or placeholders are fragments, not complete runnable applications. Configuration values are illustrative, not universal tuning recommendations.

Cheatsheets remains the home for language/framework syntax and technology-specific references, including Kafka, Kubernetes/cloud, AWS/OCI, and Terraform. This folder explains cross-service/system tradeoffs and links back rather than replacing them.

[Back to repository overview](../README.md)
