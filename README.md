# Interview Preparation

A personal interview-preparation repository covering coding problems, language fundamentals, backend frameworks, frontend fundamentals, databases, OOP, and practical senior-level system design.

## Folder structure

```text
InterviewPrep/
├── README.md          — home and topic navigation
├── Cheatsheets/       — languages, frameworks, databases, cloud, and tools
├── System_Design/     — architecture, scaling, reliability, and security
├── DSA/               — Python and Java coding exercises
├── Projects/          — actual architecture, contributions, and interview stories
│   ├── EventOps/
│   ├── PeopleSoft/
│   └── Gordian/
├── Questions/         — technical and behavioural interview practice
└── References/        — supporting technical reference documents
```

## Scenario practice

- [Technical interview questions](Questions/Questions.md) cover backend APIs, data and SQL, Python, AWS, and fraud detection.
- [System design interview questions](Questions/System_Design_Questions.md) cover chatbots, food delivery, centralized logging, and notifications.
- [Behavioural interview questions](Questions/Behavioural.md) cover end-to-end feature design, disagreements, production incidents, bug troubleshooting, and mentoring or feature leadership.

## Languages and fundamentals

| Content | What it contains |
|---|---|
| [DSA practice programs](DSA) | Individual Python and Java solutions for arrays/strings, binary search, linked lists, trees, graphs, heaps, tries, dynamic programming, sorting, and related problems |
| [DSA cheatsheet](Cheatsheets/DSA.md) | Algorithm/data-structure revision, patterns, complexity, and examples |
| [Python cheatsheet](Cheatsheets/Python.md) | Language/runtime behavior, collections, OOP, concurrency, memory, testing, and backend interview questions |
| [Java cheatsheet](Cheatsheets/Java.md) | JVM, versions, collections, generics, streams, concurrency, memory, profiling, JUnit testing, and senior practical questions |
| [Frontend cheatsheet](Cheatsheets/Frontend_Angular_React.md) | DOM/tree structure, React Hooks, components, side effects, Promises/async-await, Angular/TypeScript, RxJS, forms, routing, HTML/CSS, browser storage/security, accessibility, and practical interview questions |
| [OOP cheatsheet](Cheatsheets/OOP.md) | Encapsulation, polymorphism, inheritance/composition, SOLID, patterns, and design exercises |

## Backend and data

| Content | What it contains |
|---|---|
| [Django and Flask cheatsheet](Cheatsheets/Django_Flask.md) | Framework behavior, ORM, migrations/indexing, authentication, APIs, Celery integration links, testing, and performance |
| [Celery](Cheatsheets/Celery.md) | Task APIs, broker/worker/results, Canvas, retries, acknowledgement, routing, Beat, and operations |
| [Redis](Cheatsheets/Redis.md) | Data structures, threading, transactions, TTL, eviction, persistence, replication, and sharding |
| [Spring Boot cheatsheet](Cheatsheets/SpringBoot.md) | Dependency injection, proxies, transactions, JPA, security, reliability, testing, and production diagnosis |
| [Database cheatsheet](Cheatsheets/Database.md) | SQL, schema design, indexes, transactions/isolation, replication, read replicas, partitioning/sharding, NoSQL, and recovery |

## System design and project experience

| Content | What it contains |
|---|---|
| [Networking fundamentals](System_Design/Networking.md) | DNS, TCP/UDP, TLS, HTTP, CIDR, routing, proxies, latency, and troubleshooting |
| [System design study index](System_Design/README.md) | 17 architecture guides, technology companion links, suggested study order, and practical design exercises |
| [Project interview guides](Projects/README.md) | PeopleSoft Cloud Manager, EventOps, and Gordian; architecture, distributed-system failures, scaling, personal contributions, and interview Q&A |

## Cloud, infrastructure, and technology guides

| Guide | What it contains |
|---|---|
| [Linux and Bash](Cheatsheets/Linux.md) | Slow-process investigations, CPU/memory/disk diagnosis, processes/signals, logs, networking, shell scripting, cron, and practical interview exercises |
| [Nginx](Cheatsheets/Nginx.md) | Request routing, proxy_pass paths, headers/TLS, upstreams, streaming, and diagnostics |
| [Terraform](Cheatsheets/Terraform.md) | Providers, execution, state, locking, drift, and OCI provisioning |
| [Kafka and messaging](Cheatsheets/Kafka.md) | Brokers, partitions, consumer groups, offsets, ordering, and delivery semantics |
| [Kubernetes](Cheatsheets/Kubernetes.md) | Pods, control plane, workloads, probes, resources, autoscaling, networking, and rollouts |
| [AWS interview preparation](Cheatsheets/AWS.md) | EC2, S3, IAM, databases, messaging, networking, monitoring, and recovery |
| [OCI vs. AWS](Cheatsheets/OCI_vs_AWS.md) | Service mappings, cloud tradeoffs, availability, and cost |
| [Technology comparisons](Cheatsheets/Technology_Comparisons.md) | Responsibilities and differences across backend and cloud tools |
| [MongoDB](Cheatsheets/MongoDB_NoSQL.md) | Document modeling, queries, indexes, and performance |

Cheatsheets covers languages, frameworks, and specific technologies. System_Design covers architecture, scaling, reliability, and cross-system decisions. Projects holds actual project context, contribution stories, and evidence boundaries, with links to the relevant guides.

## System design coverage

- **Performance:** Redis/caching/CDN, memory profiling, consistent hashing, Bloom filters, approximate data structures, rate limiting.
- **Communication and correctness:** Kafka/queues, delivery semantics, REST, microservices, consistency/quorum, distributed locks, leader election, Saga/outbox.
- **Identity and security:** JWT, OAuth/OIDC/PKCE, RBAC, browser storage/cookies, password hashing/bcrypt, encryption, Shamir sharing, secrets rotation, tenant isolation.
- **Platform and operation:** Kubernetes, containers, storage/networking, AWS ingress/egress and security groups/NACLs, autoscaling, observability/SLOs, Terraform/OpenTofu, CI/CD, disaster recovery.
- **Project-oriented design:** search/reindexing, durable cloud workflows, large-data/Celery pipelines, RAG/AI agents, and design patterns.

See the [full topic map](System_Design/README.md#topic-map) for all files.

## Fast track for senior backend interviews

1. [Microservices, scaling, and distributed systems study track](System_Design/README.md#priority-track-microservices-scaling-and-distributed-systems).
2. [EventOps architecture and migration](Projects/EventOps/02_Architecture_and_Data_Flow.md) — service boundaries, shared data, Celery, and tenant isolation.
3. [Cloud Manager distributed orchestration](Projects/PeopleSoft/02_Architecture_and_Data_Flow.md) — lifecycle state, partial failures, and recovery.
4. [Gordian worker and data pipeline architecture](Projects/Gordian/02_Architecture_and_Data_Flow.md) — memory, cache scope, and background scaling.

## Frontend interview fast track

Start with the [frontend questions from recent interviews](Cheatsheets/Frontend_Angular_React.md). Follow its Fundamentals → Angular → React sections. Practice shared browser/JavaScript concepts first, then framework questions and request-race scenarios, connecting answers to your actual project responsibilities.

## Revision priority

- **Daily revision:** core language/framework questions, SQL, API/security fundamentals, and project introductions.
- **Deeper reference:** implementation examples, architecture diagrams, and failure exercises linked from those answers.
- **Optional depth:** explicitly labeled specialist topics; revisit when a role or interview requires them.
- **Unfinished notes:** use the single [project details-to-recall checklist](Projects/README.md#details-to-recall).

For spoken answers use **problem → mechanism → example → tradeoff → result/evidence**. Use “I did” for recorded experience and “I would” for design exercises. Keep unknown metrics and implementation details in the recall checklist instead of filling gaps with guesses.

## How to use the material

1. Review the relevant language/framework and database fundamentals.
2. Solve problems in `DSA/`; explain assumptions, complexity, edge cases, and alternatives.
3. Follow the [system design study order](System_Design/README.md#suggested-study-order).
4. Practice a real scenario aloud using mechanism → example → tradeoff → failure → evidence.
5. Prepare project-specific stories with actual architecture, personal contribution, and measured outcomes.

Cheatsheets include focused snippets, comparison tables, failure cases, and deeper follow-ups. Many examples intentionally omit application collaborators/imports or use placeholders; they are study material rather than deployable production configurations. Product defaults and APIs can vary by version; consult linked primary documentation for the deployed stack.

Practice solutions are individual exercises and may have different input/entry-point conventions. This repository does not provide a single unified application or test runner.
