# Interview Preparation

A personal interview-preparation repository covering coding problems, language fundamentals, backend frameworks, databases, OOP, and practical senior-level system design.

## Repository guide

| Content | What it contains |
|---|---|
| [DSA practice programs](DSA/) | Individual Python and Java solutions for arrays/strings, binary search, linked lists, trees, graphs, heaps, tries, dynamic programming, sorting, and related problems |
| [DSA cheatsheet](DSA_CheatSheet.md) | Algorithm/data-structure revision, patterns, complexity, and examples |
| [Python cheatsheet](Python_CheatSheet.md) | Language/runtime behavior, collections, OOP, concurrency, memory, testing, and backend interview questions |
| [Java cheatsheet](Java_CheatSheet.md) | JVM, versions, collections, generics, streams, concurrency, memory, profiling, and senior practical questions |
| [OOP cheatsheet](OOP_CheatSheet.md) | Encapsulation, polymorphism, inheritance/composition, SOLID, patterns, and design exercises |
| [Django and Flask cheatsheet](Django_Flask_CheatSheet.md) | Framework behavior, ORM, migrations/indexing, authentication, APIs, background work, testing, and performance |
| [Spring Boot cheatsheet](SpringBoot_CheatSheet.md) | Dependency injection, proxies, transactions, JPA, security, reliability, testing, and production diagnosis |
| [Database cheatsheet](Database_CheatSheet.md) | SQL, schema design, indexes, transactions/isolation, replication, read replicas, partitioning/sharding, NoSQL, and recovery |
| [System design study index](System_Design/README.md) | 19 focused cheatsheets, suggested study order, resume deep dives, and practical design exercises |
| [Project interview guides](Projects/README.md) | Project narratives, architecture walkthroughs, personal contributions, and interview Q&A; starting with EventOps |

## System design coverage

- **Performance:** Redis/caching/CDN, memory profiling, consistent hashing, Bloom filters, approximate data structures, rate limiting.
- **Communication and correctness:** Kafka/queues, delivery semantics, REST, microservices, consistency/quorum, distributed locks, leader election, Saga/outbox.
- **Identity and security:** JWT, OAuth/OIDC/PKCE, RBAC, browser storage/cookies, password hashing/bcrypt, encryption, Shamir sharing, secrets rotation, tenant isolation.
- **Platform and operation:** Kubernetes, containers, storage/networking, autoscaling, observability/SLOs, Terraform/OpenTofu, CI/CD, disaster recovery.
- **Project-oriented design:** search/reindexing, durable cloud workflows, large-data/Celery pipelines, RAG/AI agents, and design patterns.

See the [full topic map](System_Design/README.md#topic-map) for all files.

## How to use the material

1. Review the relevant language/framework and database fundamentals.
2. Solve problems in `DSA/`; explain assumptions, complexity, edge cases, and alternatives.
3. Follow the [system design study order](System_Design/README.md#suggested-study-order).
4. Practice a real scenario aloud using mechanism → example → tradeoff → failure → evidence.
5. Prepare project-specific stories with actual architecture, personal contribution, and measured outcomes.

Cheatsheets include focused snippets, comparison tables, failure cases, and deeper follow-ups. Many examples intentionally omit application collaborators/imports or use placeholders; they are study material rather than deployable production configurations. Product defaults and APIs can vary by version; consult linked primary documentation for the deployed stack.

Practice solutions are individual exercises and may have different input/entry-point conventions. This repository does not provide a single unified application or test runner.
