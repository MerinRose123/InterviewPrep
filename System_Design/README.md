# System Design Interview Preparation

Practical senior-engineer revision: **19 topic cheatsheets plus this index**. Each sheet combines mechanisms, examples, tradeoffs, failure scenarios, verification, and deeper follow-up questions. Diagrams/configuration are explanatory; placeholders and example numbers must be adapted and measured before use.

## Topic map

| Cheatsheet | What to study |
|---|---|
| [Caching and performance](Caching_Performance_CheatSheet.md) | Redis, cache-aside, TTL, eviction, stampede, invalidation, CDN |
| [Messaging and Kafka](Messaging_Kafka_CheatSheet.md) | Architecture, partitions, consumer groups, offsets, ordering, retries, DLQ, delivery semantics |
| [Authentication and authorization](Authentication_Authorization_CheatSheet.md) | Sessions/JWT, RBAC/ABAC, OAuth 2.0, OIDC, PKCE, refresh/revocation |
| [Browser storage and security](Browser_Storage_Security_CheatSheet.md) | localStorage/sessionStorage/cookies, JWT placement, XSS, CSRF, CORS, BFF |
| [Cryptography, passwords, and secrets](Cryptography_Passwords_Secrets_CheatSheet.md) | Hashing/encryption/signing, password storage, bcrypt/Argon2id, salts/peppers, Shamir, rotation |
| [Distributed systems](Distributed_Systems_CheatSheet.md) | CAP, consistency, quorum, leases/fencing, leader election, 2PC, Saga |
| [Cloud and Kubernetes](Cloud_Kubernetes_CheatSheet.md) | Object storage, containers, architecture, probes, autoscaling, networking, deployment/DR |
| [Observability](Observability_CheatSheet.md) | Logs/metrics/traces/profiles, SLOs, tail latency, capacity, incident response |
| [Memory profiling and performance](Memory_Profiling_Performance_CheatSheet.md) | Leaks vs. churn, heap/RSS/native memory, Java/Python profiling, OOMKilled |
| [Multi-tenancy and security](Multi_Tenancy_Security_CheatSheet.md) | Isolation, placement, noisy neighbors, IAM, network boundaries, lifecycle/audit |
| [Microservices](Microservices_CheatSheet.md) | Boundaries, modular monolith, APIs/events, gateways, resilience, CQRS, migrations |
| [REST and API design](REST_API_Design_CheatSheet.md) | HTTP, errors, idempotency, concurrency, pagination, async jobs, webhooks/WebSockets |
| [Algorithms and data structures](Algorithms_Data_Structures_CheatSheet.md) | Consistent/rendezvous hashing, Bloom/Cuckoo filters, HLL/CMS, Merkle trees, rate limits, IDs |
| [Design patterns](Design_Patterns_CheatSheet.md) | Strategy, factory/builder, adapter/decorator/proxy, observer/state, DI, distributed patterns |
| [Search systems](Search_Systems_CheatSheet.md) | OpenSearch/Elasticsearch, mappings, shards/replicas, synchronization, live reindexing |
| [Workflow orchestration](Workflow_Orchestration_CheatSheet.md) | Durable cloud operations, idempotency, concurrency, recovery, cancellation, versions |
| [Large data and background processing](Large_Data_Background_Processing_CheatSheet.md) | CSV/PDF pipelines, Celery, chunking, acknowledgements, memory, fairness, recovery |
| [Infrastructure automation](Infrastructure_Automation_CheatSheet.md) | Terraform/OpenTofu, state/locking/drift, partial applies, CI/CD, images, cost |
| [RAG and AI agents](RAG_AI_Agents_CheatSheet.md) | Ingestion/retrieval, ACLs, tools, prompt injection, evaluation, latency/cost |

## Suggested study order

1. **Core API and data:** REST → authentication → browser storage → cryptography → [database design/indexing/isolation](../Database_CheatSheet.md).
2. **Scale and failure:** caching → algorithms → messaging/Kafka → distributed systems → microservices.
3. **Production operation:** cloud/Kubernetes → observability → memory profiling → multi-tenancy/security.
4. **Resume deep dives:** workflow orchestration → large-data processing → infrastructure automation → search → RAG/agents.
5. **Design vocabulary:** patterns alongside [OOP/SOLID](../OOP_CheatSheet.md); revisit them while explaining real projects.

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
| Tenant-aware export service | REST, background processing, memory, security | Worker dies after upload but before checkpoint |
| Cloud environment orchestrator | Workflows, infrastructure, distributed systems | Resource created but provider response lost |
| Search platform migration | Search, messaging, observability | Update/delete races during reindex |
| Login and credential platform | Auth, browser, cryptography | Token theft, refresh race, signing/secret rotation |
| Event-driven order workflow | Messaging, microservices, Saga | Payment succeeds while order confirmation fails |
| Debugging assistant | RAG, search, security | Malicious log content asks tool to reveal a secret |

## Example and source conventions

Source links point to primary documentation/specifications or original research. Rolling documentation may describe a newer version than your deployment; check the project's pinned versions. Snippets with application collaborators or placeholders are fragments, not complete runnable applications. Configuration values are illustrative, not universal tuning recommendations.

The language/framework sheets remain the home for detailed Java/Python/Django/Spring syntax. This folder explains cross-service/system tradeoffs and links back rather than replacing them.

[Back to repository overview](../README.md)
