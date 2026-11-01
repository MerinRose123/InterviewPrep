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
- Gordian: [MongoDB interview deep dive](../Cheatsheets/MongoDB.md).
- Original comprehensive project references: [EventOps](EventOps/Project_Reference.md), [PeopleSoft](PeopleSoft/Cloud_Manager.md), [Gordian](Gordian/Project_Reference.md). These preserve long-form details while the reorganized guides are refined.

## System-design connections

Use the [System Design index](../System_Design/README.md) for general mechanisms. In a project interview, start with the actual project architecture, explain a concrete challenge, then compare alternatives and walk through failure or scale.
