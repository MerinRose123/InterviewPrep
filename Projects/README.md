# Project interview preparation

Prioritize **architecture, service boundaries, scale, distributed correctness, failure recovery, and personal engineering contributions**. Each project has a consistent five-part study path. Technology-specific guides live in Cheatsheets; architecture and cross-system concepts live in System_Design. Project-specific architecture and experience stay here.

| Project | Start here | Architecture | Challenges | Scaling / failures | Interview Q&A |
|---|---|---|---|---|---|
| EventOps | [Overview](EventOps/01_Project_Overview.md) | [Architecture](EventOps/02_Architecture_and_Data_Flow.md) | [Challenges](EventOps/03_Engineering_Challenges.md) | [Failure scenarios](EventOps/04_Scaling_and_Failure_Scenarios.md) | [Q&A](EventOps/05_Interview_QA.md) |
| PeopleSoft Cloud Manager | [Overview](PeopleSoft/01_Project_Overview.md) | [Architecture](PeopleSoft/02_Architecture_and_Data_Flow.md) | [Challenges](PeopleSoft/03_Engineering_Challenges.md) | [Failure scenarios](PeopleSoft/04_Scaling_and_Failure_Scenarios.md) | [Q&A](PeopleSoft/05_Interview_QA.md) |
| Gordian | [Overview](Gordian/01_Project_Overview.md) | [Architecture](Gordian/02_Architecture_and_Data_Flow.md) | [Challenges](Gordian/03_Engineering_Challenges.md) | [Failure scenarios](Gordian/04_Scaling_and_Failure_Scenarios.md) | [Q&A](Gordian/05_Interview_QA.md) |

## Interview priority

1. **EventOps — microservices:** Django-to-Flask extraction, Nginx, shared PostgreSQL, tenant isolation, concurrent scheduling, Celery and Redis.
2. **PeopleSoft Cloud Manager — distributed orchestration:** control plane versus managed runtime, OCI lifecycle, partial failure, retries, credentials, Terraform state, search scaling.
3. **Gordian — asynchronous scaling:** 16 GB+ processing, Celery worker isolation, LRU cache scope, memory pressure, report retries, similarity analysis.

## Project references and general study links

- PeopleSoft: [Runtime architecture and distributed systems](PeopleSoft/Runtime_Architecture.md), [Terraform](../Cheatsheets/Terraform.md), [technology comparisons](../Cheatsheets/Technology_Comparisons.md), [real debugging story](PeopleSoft/Debugging_Stories.md).
- Gordian: [MongoDB interview deep dive](../Cheatsheets/MongoDB_NoSQL.md).
- PeopleSoft deeper references: [Cloud Manager orchestration](PeopleSoft/Cloud_Manager.md) and [runtime architecture](PeopleSoft/Runtime_Architecture.md). The numbered guides are the entry points; use these references for implementation depth.

## System-design connections

Use the [System Design index](../System_Design/README.md) for general mechanisms. In a project interview, start with the actual project architecture, explain a concrete challenge, then compare alternatives and walk through failure or scale.

## Details to recall

This is the single working checklist for incomplete experience details. Technical examples labeled as designs remain useful practice; they are not historical implementation claims.

| Project / story | Missing details |
|---|---|
| EventOps migration | Actual extracted services/modules, write ownership, rollout sequence, individual responsibilities |
| EventOps integration and tenancy | Calendar provider/API, SSO/session configuration, tenancy package/context selection, cross-service identity |
| EventOps reporting and deployment | Historical renderer, template engine, Beat ownership/configuration, image registry, Compose setup, report delivery |
| EventOps prefetch regression | Screen/API and relation, conditional trigger, load-test setup, observed after-fix timing and actual validation |
| EventOps testing and outcomes | Measured coverage scope/type, one real tenant-isolation regression test, definitions behind efficiency metrics |
| Gordian similarity | Input fields/parsing, fitted corpus, cleaning/n-grams, score aggregation/threshold, review examples and validation |
| Gordian reporting/cache | Production pool/concurrency, memory budget, cache keys/limits/invalidation, dataset storage, report delivery, observed runtime |
| Gordian persistence | Actual collections/indexes/query paths; practice schemas in the MongoDB guide are illustrative |
| PeopleSoft workflow/Terraform | Modules and releases changed, invocation mechanism, state/backend, operation identity, locks/retries, readiness checks |
| PeopleSoft OpenSearch/Exadata | Actual node roles/counts, add-node/reindex sequence, integration module, compatibility/connectivity issue, validation |
| PeopleSoft Vault/CI/CD | Consumer update order and recovery, actual pipeline stages, measurement inputs for time savings and cost attribution |
| PeopleSoft AI-agent work | One implemented workflow, sources/tools, permissions, evaluation, measurement behind the productivity claim |
| CLI dependency incident | Exact dependency/version/error, packaging format, Merin's individual diagnostic/fix steps, validation and outcome |
| Additional real incident | Symptom, evidence, rejected hypotheses, root cause, personal fix, regression check, and result |
