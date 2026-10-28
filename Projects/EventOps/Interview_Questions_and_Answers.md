# EventOps: interview questions and answers

**InApp | September 2019-November 2021 | Merin Rose Tom**

[Project architecture, technology stack, workflows, and contributions](Interview_Guide.md)

The project description above is followed here by introductions, structured decision deep dives, and quick revision questions. Deep dives follow mechanism → example → tradeoff → failure → evidence. Evidence states what was confirmed, what is tentative, and what would verify a proposed explanation.


### 30-second introduction

> I worked on EventOps at InApp from September 2019 to November 2021. It managed organizational event operations such as people, spaces, equipment, budgets, and reporting. I was a main contributor to migrating its Django monolith toward Flask-based microservices using Docker and Nginx. I also worked on availability-aware scheduling, email notifications, detailed PDF reports, and pytest-based testing, increasing coverage from 40% to 70%.

### Two-minute introduction

> EventOps was an event-management system I worked on across my trainee and software-engineer roles at InApp. It supported event operations including spaces, equipment, people, budgets, and reporting, with conditional workflows and role-based access.
>
> It originally used a Django monolith. I was a main contributor to moving toward Flask-based microservices. Our stack included Angular on the frontend, Python with Django and Flask on the backend, PostgreSQL for persistence, Celery and Redis for background processing, and Docker with Nginx for containerized services and routing.
>
> My feature work included email notifications, scheduling that considered participant availability, and PDF reports containing extensive event details. Another concrete contribution was improving the pytest-based unit testing framework. Coverage had been limited at about 40%; I expanded important-area coverage, using techniques such as mocking, and brought it to 70%, an increase of 30 percentage points. The project also earned me CEO appreciation.
>
> For a deeper technical discussion, I can explain the migration, how an event workflow connected to background processing, or how I made the application more testable.

### Architecture decision deep dives

Each answer follows **mechanism → example → tradeoff → failure → evidence**. Mechanism explains how the choice works; example connects it to EventOps; tradeoff identifies what it costs; failure describes what can break and the appropriate response; evidence distinguishes project facts from illustrative reasoning. Suggested mitigations below are not claims that they were implemented.

#### A1. Why was Django suitable for the original application?

**Mechanism:** Django supplies an integrated framework for database-backed applications, including models/ORM, migrations, routing, and other application facilities. That makes it a reasonable fit for a system with related business entities and consistent validation. See the [Django overview](https://docs.djangoproject.com/en/5.2/intro/overview/).

**Example:** EventOps managed users, spaces, equipment, events, and availability. These are related entities with permissions and lifecycle rules, making an integrated backend a sensible starting point.

**Tradeoff:** Shared models and conventions simplify initial development, but a growing application can couple unrelated capabilities. A modular Django application is also an alternative to service extraction; a monolith is not automatically poorly designed.

**Failure:** A change to shared data or business logic can affect several workflows. Clear module ownership, regression tests, and disciplined migrations reduce this risk. Framework choice alone does not prevent tenant leaks or slow queries.

**Evidence:** The original Django monolith and Django multi-tenancy are confirmed. The initial team's exact selection rationale and use of individual built-in components are not. Describe this as why Django fit the domain, not a verbatim historical decision you made.

#### A2. Why use Flask for extracted microservices?

**Mechanism:** Flask provides a small extensible web framework; service-specific dependencies and interfaces can be selected explicitly. Separate applications can expose bounded APIs without carrying every monolith capability. See [Flask design](https://flask.palletsprojects.com/en/stable/design/).

**Example:** A space or equipment capability can be explained as an independently packaged API behind Nginx. These are reconstructed capability boundaries, not verified names of the first services extracted.

**Tradeoff:** Explicit choices offer flexibility but require consistent validation, authorization, tenancy, errors, and configuration across services. Django could also implement those services. Flask is not inherently faster or more scalable in every workload.

**Failure:** Inconsistent permission checks or a missing tenant context in one service can undermine otherwise correct behavior. Shared interface standards and meaningful integration/security tests are possible controls.

**Evidence:** Merin's main contribution to Django-to-Flask migration, Docker packaging, and Nginx routing is confirmed. Exact service dependencies, extraction order, and measured improvements attributable to Flask remain unknown.

#### A3. Why was Nginx used?

**Mechanism:** A reverse proxy accepts a client request and forwards it to a configured backend. Path-based routing lets the frontend use an entry point while different capabilities run behind it. See [NGINX reverse proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/).

**Example:** Illustratively, `/api/spaces/` routes to the space capability and `/api/equipment/` to equipment. Angular need not know each backend's internal host and port.

**Tradeoff:** Routing is centralized and backend changes can be hidden from clients, but proxy configuration becomes an operational dependency. Application authorization still needs enforcement, and Nginx is not the Django/Flask execution server.

**Failure:** An incorrect path rewrite can produce 404s or reach the wrong backend; upstream unavailability or timeouts can appear as gateway errors. Diagnose the route, upstream connection, and application logs before retrying requests.

**Evidence:** Merin confirmed that Nginx was mainly used for routing. Production route prefixes, TLS termination, redundancy, and retry configuration have not been supplied.

#### A4. Was Nginx a gateway, reverse proxy, or load balancer?

**Mechanism:** A reverse proxy forwards traffic; an API gateway can additionally apply API policies; a load balancer distributes requests among equivalent backend instances. One product can perform several roles when configured accordingly. See [NGINX HTTP load balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/).

**Example:** Choosing the space service rather than equipment is capability routing. Choosing between two space-service replicas is load balancing. EventOps' confirmed use was the former.

**Tradeoff:** Extra gateway policies and replica balancing can improve control or capacity, but introduce configuration, health management, and shared-state considerations. They do not automatically exist because Nginx is installed.

**Failure:** A single deployed proxy could be a single point of failure; whether that risk existed depends on topology. A proxy retry of a mutating operation can duplicate work if the first backend already committed it.

**Evidence:** Say “Nginx provided reverse-proxy routing and a gateway entry point.” Do not claim production replica load balancing, centralized authentication, rate limiting, or highly available proxy deployment without evidence.

#### A5. Was REST the right mechanism for inter-service communication?

**Mechanism:** Synchronous HTTP APIs allow a caller to request data or an operation and receive a response. REST is a reasonable fit for resource-oriented interfaces and familiar Python tooling. It is a choice based on interaction requirements, not a requirement of microservices.

**Example:** A scheduling capability could request space/equipment availability and use the response to validate an event. This is an illustrative exchange; the exact historical endpoints and caller/callee relationships are not recovered.

**Tradeoff:** Request-response behavior is straightforward to understand and debug, but the caller waits for dependencies. Long call chains accumulate latency and reduce availability. Synchronous calls are appropriate when an immediate answer is necessary; report rendering and delayed notifications may not need them.

**Failure:** A downstream timeout may mean “no result observed,” not “nothing happened.” A reference client uses bounded timeouts, selective retries, request correlation, and idempotency for retriable writes. Unavailable availability data should not silently be treated as “available.”

**Evidence:** Merin tentatively recalls REST calls. Nginx routing, a common database, and Celery PDF tasks are confirmed. No service mesh, gRPC, circuit breaker, or event-streaming deployment has been established.

#### A6. What alternatives exist to synchronous REST?

**Mechanism:** Alternatives include asynchronous task queues, published business events, gRPC calls, and in-process calls when capabilities stay within one application. Direct shared-database access is another integration option with different ownership implications. gRPC defines callable service methods and commonly uses Protocol Buffers; it does not inherently remove synchronous coupling. See [gRPC concepts](https://grpc.io/docs/what-is-grpc/core-concepts/).

**Example:** Immediate availability queries can use HTTP; PDF generation can be queued; an event-confirmed notification can be handled later if business requirements permit. A high-volume internal typed interface might justify evaluating gRPC. Keeping closely coupled booking logic together can avoid an unnecessary network boundary.

**Tradeoff:** Queues allow temporal decoupling but delay outcomes and require duplicate/retry handling. Pub/sub supports multiple consumers but needs event contracts and observability. gRPC adds schema/code-generation tooling. Shared-table reads avoid an API hop but couple consumers to storage and may bypass business rules. A modular monolith simplifies transactions while reducing independent deployment boundaries.

**Failure:** Async delivery can be duplicated, delayed, or reordered; projections can be stale. Stale event-driven availability alone must not authorize a conflicting booking. gRPC calls still fail or exceed deadlines. Shared-database consumers can break on migrations.

**Evidence:** Celery/Redis and asynchronous PDF generation were used. Other options here are alternatives for discussion, not technologies used by EventOps. There is no basis to claim REST was wrong without workload or reliability evidence.

#### A7. How should service-call failures be tackled?

**Mechanism:** Bound connection/read waits within an overall request budget, classify errors, and limit retries. Use backoff/jitter for eligible transient failures and a circuit breaker or concurrency limit where recurring failures threaten callers. Retry budgets prevent every layer from amplifying load.

**Example:** If equipment availability cannot be read, return a clear “cannot validate now” result or preserve an explicitly pending workflow. Do not confirm a booking from missing data. A failed report request can be retried separately when its logical request identity is preserved.

**Tradeoff:** Fast failure protects capacity but can reject work during brief outages. Retries improve some transient outcomes but increase load and response time. Circuit breakers add state and require careful recovery behavior.

**Failure:** If A retries B three times and B retries C three times, one request can cause nine calls to C. A write timeout can also cause duplicate reservations when retried without a stable operation identity. Read-like HTTP methods are not a substitute for verifying actual idempotency.

**Evidence:** The project's real timeout, retry, and breaker configuration has not been recalled. Present these as design responses, not “what we implemented.” A concrete incident, log trace, client setting, and regression test would establish a historical answer.

#### A8. How were periodic tasks scheduled, and what could fail?

**Mechanism:** Celery Beat dispatches due periodic tasks; Celery workers execute them. Beat does not itself perform PDF rendering or business task execution. One scheduler must own a given schedule unless coordination prevents duplicates. See [Celery periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html).

**Example:** A periodic due-work scan is an illustrative EventOps use case. The fact of periodic scheduling with Beat is confirmed; the actual task list and intervals are not.

**Tradeoff:** Periodic scans can provide simple repeatable execution, but timing precision depends on scan intervals, queue delay, and worker availability. Schedule management and execution monitoring remain necessary.

**Failure:** Duplicate Beat instances can enqueue duplicates, long runs can overlap, downtime can delay dispatch, and worker queues can grow. Reference controls include one schedule owner, occurrence deduplication, safe overlap prevention, and an explicit overdue-work policy.

**Evidence:** Beat, Celery, and Redis are confirmed. Schedule storage, ownership topology, timezone settings, locks, and catch-up behavior remain unknown.

#### A9. How were background-task failures handled?

**Mechanism:** A robust task design separates transient errors from invalid input, records a logical task identity, and defines bounded retries and operator-visible failure. Acknowledgment and broker persistence settings determine recovery behavior; idempotency makes repeated execution safer. See [Celery tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

**Example:** A transient asset-fetch error during PDF generation may justify retry; a broken template generally needs a code fix. A reference report job uses a stable request ID and avoids marking completion before output is ready.

**Tradeoff:** Retries can recover without manual intervention, but consume worker capacity and can repeat external effects. More concurrency can exhaust memory if many reports render simultaneously.

**Failure:** Early acknowledgment can lose in-flight work after a worker crash; late acknowledgment can allow redelivery under relevant settings, but does not guarantee recovery from every termination. Neither makes external effects exactly once.

**Evidence:** Celery PDF processing is confirmed. Historical acknowledgment, retry, task-status, output-storage, and crash-recovery mechanisms remain unverified. Use one actual failed-task example if later recalled.

#### A10. How would SendGrid email failures be handled?

**Mechanism:** SendGrid accepts email submissions for delivery. Submission, provider processing, and recipient delivery are distinct stages. The actual EventOps integration may have used API or SMTP; that detail remains unknown. See the [SendGrid Mail Send reference](https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send).

**Example:** An event update can create notification content, then submit it to SendGrid. A successful submission does not prove the recipient read or received it in their inbox.

**Tradeoff:** A delivery provider removes much mail infrastructure work but introduces dependency on provider availability, limits, credentials, and delivery outcomes. Tracking outcomes adds integration work.

**Failure:** A network timeout after provider acceptance can make retries send duplicates. A reference design distinguishes retryable rejection from uncertain submission, tracks attempts, and uses delivery-event processing where available. It does not assume provider-side idempotency support.

**Evidence:** SendGrid use and automated email features are confirmed. Actual retry rules, callbacks/webhooks, delivery metrics, API/SMTP choice, and duplicate handling have not been supplied.

#### A11. What are the limitations of the current architecture?

**Mechanism:** Separate application services still share a database, and synchronous dependencies can couple runtime availability. A service boundary provides benefits only when contracts, ownership, and operations support it.

**Example:** A migration affecting an availability table could affect users, scheduling, and reporting. A large reporting workload could compete with transactional work for database connections or I/O, even with separate worker processes.

**Tradeoff:** The common database supported continued access during migration and avoided immediate data splitting. It also limited storage independence. An architecture may reasonably accept that tradeoff during incremental modernization.

**Failure:** Potential risks include database contention, schema-coupled releases, cascading HTTP failures, stale availability, duplicate periodic work, and tenant-context mistakes. These are risks to inspect, not confirmed incidents. A single proxy/database/Beat process would add topology-dependent failure points; deployment redundancy is unknown.

**Evidence:** Shared PostgreSQL and multiple application services are confirmed; REST is tentative. Contention, downtime, poor latency, and missing resilience controls have not been demonstrated. Validate risks using traces, query plans/locks, deployment dependencies, queue age, and isolation tests.

#### A12. What would you improve first, and how would you prove it helped?

**Mechanism:** Prioritize an observed reliability or performance problem, establish a baseline, change one relevant mechanism, and verify both correctness and operating results. A larger infrastructure stack is not automatically an improvement.

**Example:** If PDF work delays short tasks, measure queue age and render duration, then evaluate separate worker queues and concurrency limits. If REST dependencies dominate scheduling latency, measure call count and dependency timings before considering batching, boundary changes, or a read model.

**Tradeoff:** Dedicated workers consume resources; batching affects API shape; cached/projection data introduces freshness concerns. Booking correctness still needs authoritative validation. Database-per-service or Kafka would require a stronger justification than “microservices best practice.”

**Failure:** More workers can overload PostgreSQL, caching can hide stale availability, and retries can mask a persistent fault. Keep correctness checks and a reversible rollout alongside the performance comparison.

**Evidence:** These are proposed improvements. The strongest existing measured result is pytest coverage moving from 40% to 70%. New improvements need their own evidence, such as tail latency, queue wait, memory, failure/duplicate rates, and a regression test—not the unrelated approximate 15% or 20% career figures.

### Communication alternatives at a glance

| Mechanism | Fits best when | Main cost | EventOps status |
|---|---|---|---|
| REST over HTTP | Immediate resource-oriented request/response | Runtime coupling, timeouts, call-chain latency | Tentative recollection |
| Celery task queue | Work can complete later with a defined task handler | Delayed outcome, delivery/retry semantics | Confirmed for PDFs |
| Pub/sub business events | Several consumers react independently to a state change | Contract evolution, duplicates, ordering, eventual consistency | Alternative, not confirmed |
| gRPC | Typed internal RPC/streaming justifies extra tooling | Schema/tooling complexity; still network-dependent | Alternative, not confirmed |
| Shared database access | Integration retains common data during transition | Schema coupling and potential business-rule bypass | Common DB confirmed; exact cross-table access unknown |
| In-process module call | Closely coupled logic belongs in one deployment | Less independent deployment/scaling | Original monolith confirmed; possible boundary-design alternative |

**A concise response to “Was REST the right choice?”**

> REST was a reasonable choice for operations needing an immediate result, such as availability queries. The tradeoff is synchronous dependency and network failure handling. I would use background tasks for work that can finish later, like our Celery PDF generation, and consider events for independent reactions. gRPC would need a concrete contract or performance requirement. My recollection of the historical inter-service REST calls is tentative; I would verify the actual client and endpoint before claiming specific retry behavior.


### Additional interview questions and quick revision answers


#### 1. What was EventOps, and what did you do?

**Answer:** I worked on EventOps at InApp from September 2019 to November 2021. It managed organizational event operations including people, spaces, equipment, budgets, and reporting. I was a main contributor to migrating the Django monolith toward Flask microservices, and worked on email notifications, availability-aware scheduling, detailed PDF reports, and testing. My pytest improvements increased coverage from 40% to 70%.

#### 2. Explain the architecture end to end.

**Answer:** The frontend was Angular. The backend began as a Django monolith and evolved toward Flask microservices, packaged with Docker and routed through Nginx. PostgreSQL stored application data, and Celery with Redis supported background processing. I would then map one actual route and task. The services used a common PostgreSQL database, and PDF generation ran as a Celery task. Django multi-tenancy was used; schema-level isolation is my tentative recollection; exact service/table ownership and context handling need confirmation.

#### 3. What was your technology stack?

**Answer:** Python, Django and Flask for the backend; Angular and JavaScript for the frontend; PostgreSQL with Django multi-tenancy for persistence; Celery and Redis for background processing, Celery Beat for periodic scheduling, SendGrid for email; Docker for containerization; Nginx for routing; and pytest for testing. I should explain each tool through the feature or migration work I personally handled.

#### 4. Why perform work asynchronously?

**Answer:** We used Celery and Redis for background processing. PDF report generation ran as a Celery task, moving that work out of the synchronous execution path. Email task assignments still need confirmation. Asynchronous work keeps suitable long-running operations out of the request path, but requires explicit failure handling and visibility.

#### 5. How does a rule-based trigger work?

**Answer:** A trigger identifies a business occurrence, conditions decide whether it qualifies, and an action specifies the resulting work. A useful walkthrough names the original event, relevant old/new values, rule scope, and action. Whether EventOps represented these as configurable data or explicit code needs confirmation.

#### 6. How would you avoid duplicate actions?

**Design answer:** Define the identity of one logical occurrence, enforce uniqueness when recording execution, and make internal state changes safe to repeat. Include the occurrence or schedule version so later legitimate reminders are not suppressed. External email delivery still has an ambiguity window unless the provider supports suitable deduplication. I should separately describe what EventOps actually implemented.

#### 7. What if the database update succeeds but job publication fails?

**Design answer:** Dispatch after commit avoids jobs observing rolled-back state, but does not eliminate the commit-to-publication gap. A durable outbox written in the same transaction and retried by a dispatcher is one approach. I would not claim EventOps had an outbox without evidence. [Django transaction reference](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

#### 8. How did you implement RBAC?

**Answer:** RBAC is an explicit EventOps contribution. A complete personal answer needs the real roles, permission storage, enforcement point, and one allowed/denied example. The essential design principle is backend enforcement for the operation and object, in the correct tenant context; UI visibility is only a presentation concern.

#### 9. How did you prevent cross-tenant access?

**Answer:** We used Django multi-tenancy with a common PostgreSQL database. My recollection is that tenants were separated by schema, although that specific isolation mechanism still needs confirmation. Under that model, the correct schema must be selected for both requests and background tasks, with context reset on reused connections. I should explain the actual library and a real isolation test before claiming those implementation mechanisms.

#### 10. What happens when an event is rescheduled or cancelled?

**Design answer:** Execution should check the current event state and schedule identity before acting. A reschedule can invalidate an older occurrence and create a new one; cancellation should suppress obsolete work. Celery Beat and workers need compatible behavior even if old jobs remain queued. EventOps' actual mechanism is pending confirmation.

#### 11. How would you handle email failures?

**Design answer:** Classify transient and permanent failures, use timeouts and bounded retry delays, record attempts, and make exhausted failures visible. An accepted API request does not prove inbox delivery. Handle uncertain acceptance separately because retries may duplicate mail. SendGrid was the provider; the project's actual retry and delivery-tracking behavior remains to be recalled.

#### 12. Did EventOps use Celery and Redis?

**Answer:** Yes. We used Celery and Redis for background processing. Celery is the task-processing framework; Redis can serve roles such as broker or result backend, and I need to identify its actual configuration in our system. Retry and acknowledgment choices determine failure behavior; naming the tools alone does not establish those guarantees. [Celery task reference](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

#### 13. What did you improve in testing?

**Answer:** Initial coverage was around 40%. I developed and improved the pytest-based unit testing framework, expanded tests over important areas, and used mocking to isolate dependencies. Coverage reached 70%, a 30 percentage-point increase. I would substantiate this with one real tested module, the dependency mocked, and the edge case asserted. The portfolio also records Django multi-tenancy testing.

#### 14. What tests would you prioritize for automation?

**Design answer:** Conditions that should and should not fire; permission and tenant denial; cancelled or rescheduled work; duplicate execution; provider failures; and transaction rollback. Test the business logic in isolation, then verify request/worker behavior through appropriate integration tests. Browser tests cover UI behavior that a backend client cannot. [Django testing reference](https://docs.djangoproject.com/en/5.2/topics/testing/tools/).

#### 15. How was the 20% improvement measured?

**Answer:** The resume reports a 20% reduction in manual event-management effort. I need to identify the baseline, comparison workflow, and whether this was measured or estimated. Until then, I can explain which manual steps automation removed, but should not invent a measurement study.

#### 16. Was this a microservices architecture?

**Answer:** Yes. It started as a Django monolith, and I was a main contributor to migrating toward Flask-based microservices using Docker and Nginx routing. I should identify actual extracted services and their data/API contracts to explain the architecture. Separate containers by themselves do not establish independent service ownership.

#### 17. What was your hardest technical challenge?

**Answer framework:** The monolith-to-microservices migration is a confirmed engineering challenge I contributed to. I can structure the answer around an extracted capability, existing dependencies, API/data compatibility, my implementation changes, and verification. I still need a specific remembered obstacle or defect; I should not invent a production incident.

#### 18. How would you scale the application?

**Design answer:** First measure whether requests, database queries, queue delay, execution time, or provider limits are the bottleneck. Improve query shape and indexes where needed, separate suitable background workloads, and increase concurrency within downstream limits. Tenant fairness matters if one customer's work can consume the entire queue. This is a design discussion, not a claim about changes I delivered.

#### 19. What would you improve today?

**Design answer:** I would assess existing gaps before proposing changes. Candidate improvements include clearer execution history, stronger duplicate suppression, safer dispatch, tenant-isolation regression tests, and visibility into overdue work. I would prioritize the observed failure or support burden and avoid claiming those capabilities were absent without evidence.

#### 20. How do you separate your contribution from the team's?

**Answer:** My confirmed work includes a major contribution to the Django-to-Flask microservices migration, email notifications, participant-availability-aware scheduling, detailed PDF reports, and pytest framework improvements using mocking. I can quantify testing as 40% to 70% coverage. I would name the exact module and change I owned, and distinguish shared architecture decisions from my implementation.

#### 21. Why migrate from Django to Flask?

**Answer:** I contributed to moving a Django monolith toward Flask microservices for a more modular backend; scalability and modular development are documented goals. Flask suited the chosen service approach, but it is not inherently more scalable than Django. A strong answer needs the actual business capability extracted and the original maintenance or delivery problem. Django can also power microservices, and Flask can also be used in a monolith.

#### 22. What did Docker and Nginx contribute?

**Answer:** Docker packaged backend services into consistent runtime units, while Nginx routed incoming requests to the appropriate backend. I should support this with a real service and route from the migration. Neither Docker nor Nginx automatically provides service ownership, correct authorization, database isolation, or high availability.

#### 23. How did participant availability affect scheduling?

**Answer:** Our scheduling feature checked participant availability from an out-of-office calendar. I need to recall the calendar integration and whether we searched for slots or validated a selected slot. An out-of-office check alone does not establish absence of other meetings. For a conceptual overlap check, two half-open intervals overlap if each starts before the other ends. Concurrent scheduling requires protection beyond a pre-save availability query; the mechanism we used remains to be recalled.

#### 24. How did PDF generation work?

**Answer:** I worked on PDF reports containing extensive event details. A complete walkthrough should identify the requested event, authorization, data assembly, PDF library, and how users received the file. PDF generation ran as a Celery task. We populated an HTML template with event contents and converted it to PDF. I use WeasyPrint personally and can explain its implementation, but the historical EventOps renderer is not verified. I should not attach the separate 16 GB CSV pipeline to this story without evidence.

#### 25. What does 40% to 70% coverage mean?

**Answer:** It is an increase of 30 percentage points, or 75% relative to the original coverage. In interviews I would say “from 40% to 70%” to avoid ambiguity. I improved the pytest framework, used mocking, and expanded important-area tests. I should also explain the measured scope and one meaningful regression case, because coverage alone does not establish correctness.

#### 26. How did you manage transactions after splitting services?

**Answer:** The backend services used a common PostgreSQL database, so I should discuss the actual table/write ownership and migration coupling. A common database does not automatically make writes from separate service requests one atomic transaction. I need to recall the real transaction boundaries. Outbox patterns or compensation are possible designs, not confirmed EventOps features.
