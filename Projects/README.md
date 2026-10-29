# Project interview preparation

Prioritize **architecture, service boundaries, scale, distributed correctness, failure recovery, and personal engineering contributions**. Each project has a consistent five-part study path. The original comprehensive references remain accessible until consolidation and link checks are complete.

| Project | Start here | Architecture | Challenges | Scaling / failures | Interview Q&A |
|---|---|---|---|---|---|
| EventOps | [Overview](EventOps/01_Project_Overview.md) | [Architecture](EventOps/02_Architecture_and_Data_Flow.md) | [Challenges](EventOps/03_Engineering_Challenges.md) | [Failure scenarios](EventOps/04_Scaling_and_Failure_Scenarios.md) | [Q&A](EventOps/05_Interview_QA.md) |
| PeopleSoft Cloud Manager | [Overview](peoplesoft/01_Project_Overview.md) | [Architecture](peoplesoft/02_Architecture_and_Data_Flow.md) | [Challenges](peoplesoft/03_Engineering_Challenges.md) | [Failure scenarios](peoplesoft/04_Scaling_and_Failure_Scenarios.md) | [Q&A](peoplesoft/05_Interview_QA.md) |
| Gordian | [Overview](Gordian/01_Project_Overview.md) | [Architecture](Gordian/02_Architecture_and_Data_Flow.md) | [Challenges](Gordian/03_Engineering_Challenges.md) | [Failure scenarios](Gordian/04_Scaling_and_Failure_Scenarios.md) | [Q&A](Gordian/05_Interview_QA.md) |

## Interview priority

1. **EventOps — microservices:** Django-to-Flask extraction, Nginx, shared PostgreSQL, tenant isolation, concurrent scheduling, Celery and Redis.
2. **PeopleSoft Cloud Manager — distributed orchestration:** control plane versus managed runtime, OCI lifecycle, partial failure, retries, credentials, Terraform state, search scaling.
3. **Gordian — asynchronous scaling:** 16 GB+ processing, Celery worker isolation, LRU cache scope, memory pressure, report retries, similarity analysis.

## Specialized technical references

- PeopleSoft: [Runtime architecture and distributed systems](peoplesoft/PeopleSoft_Architecture_and_Distributed_Systems.md), [Terraform](peoplesoft/Terraform_Interview_Guide.md), [technology comparisons](peoplesoft/Technology_Comparisons.md), [real debugging story](peoplesoft/Debugging_Stories.md).
- Gordian: [MongoDB interview deep dive](Gordian/MongoDB_Interview_Deep_Dive.md).
- Original comprehensive project references: [EventOps](EventOps/Interview_Guide.md), [PeopleSoft](peoplesoft/Cloud_Manager_Interview_Guide.md), [Gordian](Gordian/Interview_Guide.md). These preserve long-form details while the reorganized guides are refined.

## System-design connections

Use the [System Design index](../System_Design/README.md) for general mechanisms. In a project interview, start with the actual project architecture, explain a concrete challenge, then compare alternatives and walk through failure or scale.
