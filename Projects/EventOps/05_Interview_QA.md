# EventOps: interview questions and answers

**InApp | September 2019-November 2021 | Merin Rose Tom**

[Project architecture, technology stack, workflows, and contributions](01_Project_Overview.md)

The project description above is followed here by introductions, structured decision deep dives, and quick revision questions. Deep dives follow mechanism → example → tradeoff → failure → evidence. Evidence states what was confirmed, what is tentative, and what would verify a proposed explanation.


### 30-second introduction

> I worked on EventOps at InApp from September 2019 to November 2021. It managed organizational event operations such as people, spaces, equipment, budgets, and reporting. I was a main contributor to migrating its Django monolith toward Flask-based microservices using Docker and Nginx. I also worked on availability-aware scheduling, email notifications, detailed PDF reports, and pytest-based testing, increasing coverage from 40% to 70%.

### Two-minute introduction

> EventOps was an event-management system I worked on across my trainee and software-engineer roles at InApp. It supported event operations including spaces, equipment, people, budgets, and reporting, with conditional workflows and role-based access.
>
> It originally used a Django monolith. I was a main contributor to moving toward Flask-based microservices. Our stack included Angular, Django/Flask, PostgreSQL accessed mainly through Django ORM with Q/F expressions, Celery/Redis and Beat, and SendGrid. We deployed per-service Docker images on EC2; generated PDFs were uploaded to S3.
>
> My feature work included email notifications, scheduling that considered participant availability, and PDF reports containing extensive event details. Another concrete contribution was improving the pytest-based unit testing framework. Coverage had been limited at about 40%; I expanded important-area coverage, using techniques such as mocking, and brought it to 70%, an increase of 30 percentage points. The project also earned me CEO appreciation.
>
> For a deeper technical discussion, I can explain the migration, how an event workflow connected to background processing, or how I made the application more testable.

### Architecture decision deep dives

Use the shared [practice method](../../README.md#revision-priority). Evidence labels distinguish actual project details from proposed designs.

#### A1. Why was Django suitable for the original application?

**Mechanism:** Django supplies an integrated framework for database-backed applications, including models/ORM, migrations, routing, and other application facilities. That makes it a reasonable fit for a system with related business entities and consistent validation. See the [Django overview](https://docs.djangoproject.com/en/5.2/intro/overview/).

**Example:** EventOps managed users, spaces, equipment, events, and availability. These are related entities with permissions and lifecycle rules, making an integrated backend a sensible starting point.

**Tradeoff:** Shared models and conventions simplify initial development, but a growing application can couple unrelated capabilities. A modular Django application is also an alternative to service extraction; a monolith is not automatically poorly designed.

**Failure:** A change to shared data or business logic can affect several workflows. Clear module ownership, regression tests, and disciplined migrations reduce this risk. Framework choice alone does not prevent tenant leaks or slow queries.

**Evidence:** The original Django monolith and Django multi-tenancy are confirmed. The initial team's exact selection rationale and use of individual built-in components are not. Describe this as why Django fit the domain, not a verbatim historical decision you made.

#### A2. Why use Flask for extracted microservices?

**Mechanism:** Flask provides a small extensible web framework; service-specific dependencies and interfaces can be selected explicitly. Separate applications can expose bounded APIs without carrying every monolith capability. See [Flask design](https://flask.palletsprojects.com/en/stable/design/).

**Example:** Feature management in the Django monolith had become difficult, changes caused regressions in other areas, and testing was becoming harder. Extracting bounded capabilities aimed to make changes easier to contain. Space/equipment service names remain reconstructed rather than verified extraction history.

**Tradeoff:** Explicit choices offer flexibility but require consistent validation, authorization, tenancy, errors, and configuration across services. Django could also implement those services. Flask is not inherently faster or more scalable in every workload.

**Failure:** Inconsistent permission checks or a missing tenant context in one service can undermine otherwise correct behavior. Shared interface standards and meaningful integration/security tests are possible controls.

**Evidence:** Merin's main contribution to Django-to-Flask migration, Docker packaging, and Nginx routing is confirmed. Exact service dependencies, extraction order, and measured improvements attributable to Flask remain unknown.

#### A3. Why was Nginx used?

Configuration examples and diagnostics: [Nginx guide](../../Cheatsheets/Nginx.md).

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

**Example:** Upcoming-event reminders are a confirmed periodic use case. A due-reminder scan is one possible implementation: find eligible events, recheck their status, and trigger notifications. The actual query, lead time, interval, and task split are not recalled.

**Tradeoff:** Periodic scans can provide simple repeatable execution, but timing precision depends on scan intervals, queue delay, and worker availability. Schedule management and execution monitoring remain necessary.

**Failure:** Duplicate Beat instances can enqueue duplicates, long runs can overlap, downtime can delay dispatch, and worker queues can grow. Reference controls include one schedule owner, occurrence deduplication, safe overlap prevention, and an explicit overdue-work policy.

**Evidence:** Beat, Celery, Redis, and upcoming-event reminders are confirmed. SendGrid handled email delivery. Schedule storage, intervals, ownership topology, timezone settings, locks, task decomposition, and catch-up behavior remain unknown.

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

#### A13. Why move from a monolith to microservices, and was it justified?

**Mechanism:** Capability boundaries reduce how much application behavior must change together. Explicit interfaces can make ownership and focused testing clearer. They do not eliminate shared-data dependencies.

**Example:** EventOps had many features to manage, changes caused regressions in other areas, and testing was becoming difficult. These were the actual migration drivers. Merin was a main contributor to the Django-to-Flask service migration.

**Tradeoff:** Smaller application boundaries can make work more manageable, but introduce network failures, interface compatibility, configuration, and integration testing. A modular monolith could also improve boundaries without distributed-operation costs. Additional possible benefits—separate releases, workload-specific scaling, clearer team ownership—are conditional, not confirmed achievements.

**Failure:** Moving tightly coupled code into separate containers without controlling dependencies can produce a distributed monolith. Shared-table changes may still trigger cross-service regressions; testing cannot stop at isolated units.

**Evidence:** The management, regression, and testing difficulties are directly confirmed. There is no measured reduction in regressions or release time supplied after migration. The 40%-70% coverage improvement is a separate testing result, not proof that microservices caused the improvement.

**Spoken answer:** “We moved because the growing feature set was becoming difficult to manage. Changes in one area introduced regressions elsewhere, and testing was harder. We wanted clearer capability boundaries and more focused changes. I contributed substantially to extracting Flask-based services. The tradeoff was more integration and network complexity, and our shared database meant we still had coupling to manage.”

#### A14. How were authentication and authorization handled?

**Mechanism:** EventOps supported both SSO login and manual login, using Django authentication mechanisms for application identity. Decorators protected admin-specific APIs in backend code, checking access before privileged view logic. Authentication and permission checks are distinct responsibilities.

**Example:** A logged-in non-admin user should not be able to invoke an admin-only API merely by bypassing Angular and calling the URL directly. Backend decorator protection is confirmed; this denied-request example is an explanatory test case, not a recalled endpoint.

**Tradeoff:** Reusing Django avoids inventing an identity system, and decorators make protected endpoints explicit. Per-endpoint decoration requires consistent coverage and review. Exact login/session settings, decorator names, and their behavior in Flask services remain unknown.

**Failure:** An omitted decorator can leave an endpoint exposed. A decorator that checks only login is insufficient for admin access; an admin check alone may not establish tenant/object scope. Suggested checks cover unauthenticated, authenticated non-admin, authorized admin, and wrong-tenant requests. Redirect versus API error behavior depends on the implementation.

**Evidence:** Django auth, RBAC, and decorator-protected admin APIs are confirmed by Merin. Do not assert JWT, particular built-in decorators, group mappings, or centralized Nginx authentication without confirmation. See [Django authentication](https://docs.djangoproject.com/en/5.2/topics/auth/default/).

**Spoken answer:** “We supported SSO and manual login, and used Django's authentication mechanisms for user identity. Admin-specific APIs were protected with decorators in the backend, so access was enforced in code rather than only by hiding UI controls. We also had a multi-tenant architecture, making tenant scope a separate concern. I would verify the exact decorator and how identity was propagated into Flask before naming that mechanism.”

#### A15. How did SSO login relate to calendar access?

**Mechanism:** SSO was an initial login option alongside manual login. Calendar retrieval is a separate integration: successful login alone does not grant calendar-data access. The historical data-access mechanism is not remembered.

**Example:** Scheduling checked the user's out-of-office information to assess availability. This does not establish a full meeting-calendar conflict check or identify a specific calendar provider.

**Tradeoff:** Organization identity integration can simplify access, while adding dependency on the identity/calendar integration's availability and granted permissions. Reusing EventOps user identity across all services is not implied by this integration.

**Failure:** Expired access, denied permissions, or provider downtime can prevent availability checks. A safe reference behavior is to expose an unavailable/unknown result rather than treat a failed lookup as “free.” Historical refresh, retries, and fallback behavior remain unknown.

**Evidence:** SSO/manual login and out-of-office availability checks are confirmed. Earlier recollection linked SSO to calendar access, but that connection is not established. Protocol, provider, API, credentials/scopes, and token lifecycle remain unknown. Do not substitute OAuth/OIDC, SAML, JWT, or a Microsoft/Google integration based solely on the term SSO.

#### A16. How did the application communicate with the database?

**Mechanism:** We mainly used Django ORM models and QuerySets to read and write the common PostgreSQL database. `Q` objects supported complex boolean conditions, and `F` expressions supported database-side field references and calculations.

**Example:** A resource search could combine alternative conditions with `Q`; comparing actual cost to a budget field illustrates `F`. These examples explain the tools; the specific historical expressions are not recalled.

**Tradeoff:** ORM code integrates well with models and reduces repetitive SQL, but query efficiency still depends on the generated SQL, relationships, indexes, and data accessed. Raw SQL is an option when a measured need justifies it, not an automatic upgrade.

**Failure:** Unbounded eager loading, per-object queries, broad updates, or missing tenant scope can still occur. Our actual prefetch change caused a roughly 10-second loading delay in load testing; I fixed it by moving optional fetching to a conditional later call.

**Evidence:** Django ORM, Q/F use, and the prefetch regression/fix are confirmed. The per-Flask-service ORM integration, exact schema, and query plans remain unverified. [Django queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/).

**Spoken answer:** “We mainly used Django ORM for PostgreSQL communication. For complex conditions we used Q objects, and for field-based expressions we used F. I still evaluated performance against the access pattern: my prefetch optimization reduced the intended number of calls but caused a load-test regression, which I fixed with conditional fetching.”

#### A17. What is the difference between Q and F? Can F prevent races?

**Mechanism:** `Q` composes predicates; `F` refers to a field within an expression. A database-side update such as `count=F('count') + 1` avoids a Python read-modify-write increment. See [Django expressions](https://docs.djangoproject.com/en/5.2/ref/models/expressions/).

**Example:** “Status is planned OR confirmed” is a Q-style condition. “Actual cost exceeds budget” is a field-comparison F-style expression. These are illustrative domain conditions, not recovered queries.

**Tradeoff:** Expressions move suitable work into SQL, but still require a correct predicate and transaction boundary. F is not a general-purpose concurrency solution.

**Failure:** Incrementing a field safely does not prove an equipment-capacity invariant or prevent overlapping space reservations. Those require suitable conditions, constraints, or transaction coordination across all competing writers.

**Evidence:** Q/F usage is confirmed. No specific race fixed with F, inventory update, or production expression is asserted. A strong follow-up would identify one actual query Merin remembers.

#### A18. How were generated PDFs stored and retrieved?

**Mechanism:** A Celery task generated a PDF from populated HTML, and the report was uploaded to an Amazon S3 bucket. Download handling is a separate application concern.

**Example:** The confirmed pipeline is event contents → HTML template → PDF generation → S3 upload. A reference object key might include tenant, event, and report identity; the actual key format is unknown.

**Tradeoff:** Object storage separates report persistence from replaceable containers, but adds upload failures, access policy, object lifecycle, and link authorization considerations. Listing or guessing an object key must not substitute for checking user access.

**Failure:** PDF rendering may succeed while upload fails, or upload may succeed before a report-status write fails. A reference design marks readiness only after upload success and can reconcile orphaned objects or stale job records. These controls are not confirmed historical features.

**Evidence:** Celery generation and S3 upload are confirmed. SDK/library, database metadata, object keys, bucket policy, and download method remain unspecified.

#### A19. How would you secure S3 report access and credentials?

**Mechanism:** A reference design keeps reports private, checks application user/tenant permissions, and either streams the file through an authorized backend or creates a short-lived presigned download URL. An EC2 instance role is an option for AWS credentials, not a confirmed EventOps configuration.

**Example:** After confirming a user's access to an event, the backend can issue a URL limited to that report. The S3 key should come from trusted report metadata rather than an unrestricted user-supplied path.

**Tradeoff:** Presigned download reduces application file-serving work, but possession of the URL grants its access until expiration or credential/policy changes make it invalid. Backend streaming provides a different control point at the cost of application bandwidth and processing.

**Failure:** A leaked URL, overly broad IAM permission, or wrong-tenant object mapping can expose reports. Naming prefixes alone do not enforce isolation. Avoid printing sensitive signed URLs or baking AWS keys into images.

**Evidence:** S3 storage and EC2 hosting are confirmed; presigned URLs, instance roles, encryption settings, and access policies are alternatives to explain, not historical claims. [AWS S3 presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html).

#### A20. How were the services built and deployed?

**Mechanism:** We used Docker images for each service. `docker build` built the service image from its Dockerfile/build context, and containers ran the service on EC2. Nginx mainly routed traffic to the relevant service.

**Example:** Illustrative only: `docker build -t eventops-spaces:example ./spaces` builds a tagged space-service image. Replacing a running service also needs the correct runtime configuration, networking, and application readiness; building alone is not deployment.

**Tradeoff:** Per-service images package dependencies consistently and enable targeted service changes. They also require image version management, compatibility testing, configuration, and cleanup.

**Failure:** Wrong image tags, missing runtime variables, dependency differences, incompatible migrations, or duplicate Beat schedulers can break a release. Suggested controls include known image versions, smoke checks, compatible migrations, graceful worker handling, and rollback planning.

**Evidence:** Per-service images, Docker builds/deployment, EC2 hosting, and Nginx routing are confirmed. Docker Compose is recalled for multi-container deployment. Registry, build location, exact Compose YAML/version, CI/CD, and zero-downtime release mechanics remain unknown. [Docker build overview](https://docs.docker.com/build/concepts/overview/).

#### A21. What did EC2 provide, and how would you scale or roll back?

**Mechanism:** EC2 supplied application compute; Docker ran services; PostgreSQL held application data; S3 stored generated PDFs. This does not establish where PostgreSQL ran or whether EC2 instances were replicated.

**Example:** A reference scale-out adds service replicas and suitable traffic distribution, while background capacity is adjusted separately. EventOps Nginx was mainly for routing; production replica balancing is not confirmed.

**Tradeoff:** More containers or instances increase capacity only when CPU, memory, database connections, and downstream limits permit it. Rolling back an image is simpler when schema and task interfaces remain compatible.

**Failure:** Adding replicas can exhaust database capacity; reverting code after a destructive migration may fail. Report objects in S3 survive a container replacement, but application references and permissions must remain correct. In-flight Celery tasks also require release compatibility.

**Evidence:** EC2, Docker, S3, and the common database are confirmed. Instance count/type, load balancer, Auto Scaling, managed database use, and actual rollback mechanism remain unknown. These are design options to evaluate against observed demand.

#### A22. Explain SSO behind the scenes.

**Mechanism:** The application delegates authentication to a trusted identity provider, validates the returned result, maps it to a local user, and establishes application login. In an OIDC code-flow example, the browser receives a code at a registered callback and the backend exchanges it before validating the identity token. SAML uses a different assertion flow. See the [step-by-step walkthrough](02_Architecture_and_Data_Flow.md#sso-behind-the-scenes-reference-walkthrough).

**Example:** A user chooses SSO in Angular, authenticates at the corporate provider, and returns to EventOps. If a provider session already exists, a repeated password prompt may be unnecessary. Manual login is the other confirmed option.

**Tradeoff:** Central identity simplifies corporate login and policies, while adding an identity-provider dependency and account/session integration work. EventOps still needs tenant membership and permission checks; a valid corporate identity alone does not authorize admin operations.

**Failure:** Invalid callbacks, expired codes, mismatched identity claims, unsafe account linking, or incorrect session handling can break login or access control. These are reference failure modes, not reported EventOps incidents. Application logout and provider logout are distinct.

**Evidence:** SSO/manual login, Django authentication, and admin decorators are confirmed. OIDC/SAML, provider, tokens, PKCE, and session details are not. Explain one reference protocol clearly while identifying it as conceptual.

**Spoken answer:** “SSO delegates identity verification to a provider the application trusts. The browser is redirected there, the provider authenticates the user, and the application validates the response before establishing local login. Roles and tenant access are still application checks. EventOps supported SSO and manual login, but I don't recall whether its integration used OIDC or SAML.”

#### A23. Why use Docker Compose, and how does its YAML work?

**Mechanism:** Compose defines services and their images/build contexts, commands, configuration, networks, and volumes in YAML. It creates containers and related resources as one application. See the [annotated example](02_Architecture_and_Data_Flow.md#docker-compose-running-the-services-together).

**Example:** Nginx, API services, Redis, Celery workers, and Beat can be started from one definition. Separate service images are confirmed; the exact historical grouping of worker/Beat images remains unknown.

**Tradeoff:** Repeatable startup reduces manual container commands, but a Compose file needs maintained configuration and dependency contracts. A single-host deployment remains dependent on that host.

**Failure:** A container can be running before it is ready. Incorrect ports, service URLs, or environment settings cause connectivity failures. Starting duplicate Beat processes can also duplicate periodic work. Startup dependencies alone do not solve runtime outages.

**Evidence:** Merin recalls Compose, per-service images, and EC2 deployment. The YAML in the project guide is a reference example, not historical configuration.

For command revision and YAML fields, see the [Compose commands](02_Architecture_and_Data_Flow.md#common-docker-compose-commands) and [YAML explanation](02_Architecture_and_Data_Flow.md#reading-the-yaml-contents).

#### A24. How did containers communicate, and why was VPC mentioned?

**Mechanism:** Compose networking can resolve container service names on the same Docker network. AWS VPC and security groups govern host-level network placement/access. Neither layer alone authenticates an API request.

**Example:** A same-host caller might reach `http://equipment:8000`. Across hosts, private routing/discovery must be configured; a local Compose service name does not automatically resolve on another EC2 instance. Nginx mainly handled frontend request routing.

**Tradeoff:** Private-network trust is simpler, but trusts any caller that can reach the endpoint through allowed paths. Service credentials or mutual TLS can strengthen caller identity, adding management overhead. Tenant/user authorization remains separate.

**Failure:** A compromised allowed container/host may call private APIs. A missing published port does not isolate services from other containers sharing their network. A VPC is not a substitute for request authorization or encryption.

**Evidence:** VPC is Merin's recalled explanation for internal connectivity, and REST calls are tentatively recalled. Exact rules and whether internal requests had no credentials are not verified.

**Spoken answer:** “Docker Compose connected the containers through a Docker network, where services could resolve each other by name. The EC2 deployment also used an AWS VPC as the network boundary. If internal calls relied on private-network trust, that restricted exposure rather than authenticating each caller. The limitation is that a compromised allowed workload can still reach internal endpoints, so service identity and tenant authorization are separate controls.”

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

**Answer:** The frontend was Angular. The backend began as a Django monolith and evolved toward Flask microservices, packaged with Docker and routed through Nginx. PostgreSQL stored application data, and Celery with Redis supported background processing. I would then map one actual route and task. The services used a common PostgreSQL database, mainly accessed through Django ORM. The application ran on EC2 with per-service Docker images; Celery-generated PDFs were uploaded to S3. Django multi-tenancy was used; schema-level isolation is my tentative recollection; exact service/table ownership and context handling need confirmation.

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

**Answer:** We supported both SSO and manual login using Django authentication mechanisms, and admin-specific APIs were protected with decorators in the backend code. Authentication identified the user; the admin checks determined whether the user could perform a privileged operation. Role-based access was part of the application. The exact decorators and role storage are not currently recalled. I would separately explain tenant and object scope, because being logged in or having an admin role does not by itself establish access to every tenant's data.

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

**Answer:** I added Django `prefetch_related()` to reduce database calls and expected faster loading. Load testing instead exposed an approximately 10-second loading delay. I also implemented the fix: removing prefetch from the initial load and fetching the additional information conditionally in a subsequent call. It resolved the loading issue, with an extra call when the data was needed. This is a load-testing performance regression I owned, not a confirmed production outage.

#### 18. How would you scale the application?

**Design answer:** First measure whether requests, database queries, queue delay, execution time, or provider limits are the bottleneck. Improve query shape and indexes where needed, separate suitable background workloads, and increase concurrency within downstream limits. Tenant fairness matters if one customer's work can consume the entire queue. This is a design discussion, not a claim about changes I delivered.

#### 19. What would you improve today?

**Design answer:** I would assess existing gaps before proposing changes. Candidate improvements include clearer execution history, stronger duplicate suppression, safer dispatch, tenant-isolation regression tests, and visibility into overdue work. I would prioritize the observed failure or support burden and avoid claiming those capabilities were absent without evidence.

#### 20. How do you separate your contribution from the team's?

**Answer:** My confirmed work includes a major contribution to the Django-to-Flask microservices migration, email notifications, participant-availability-aware scheduling, detailed PDF reports, and pytest framework improvements using mocking. I can quantify testing as 40% to 70% coverage. I would name the exact module and change I owned, and distinguish shared architecture decisions from my implementation.

#### 21. Why migrate from Django to Flask?

**Answer:** EventOps had accumulated many features, making the monolith difficult to manage. Changes in one area introduced regressions elsewhere, and testing became harder. I was a main contributor to moving toward Flask-based services with clearer capability boundaries. The goal was more manageable changes and focused testing, at the cost of network and integration complexity. Flask was the chosen service framework; the architectural benefit came from boundaries, not an inherent speed advantage over Django. The shared database meant some coupling remained.

#### 22. What did Docker and Nginx contribute?

**Answer:** Docker packaged backend services into consistent runtime units, while Nginx routed incoming requests to the appropriate backend. I should support this with a real service and route from the migration. Neither Docker nor Nginx automatically provides service ownership, correct authorization, database isolation, or high availability.

#### 23. How did participant availability affect scheduling?

**Answer:** Our scheduling feature checked participant availability from an out-of-office calendar. The application supported SSO login, but the exact calendar-data access mechanism is not recalled. The provider/protocol and whether we searched for slots or validated a selected slot remain to be recalled. An out-of-office check alone does not establish absence of other meetings. For a conceptual overlap check, two half-open intervals overlap if each starts before the other ends. Concurrent scheduling requires protection beyond a pre-save availability query; the mechanism we used remains to be recalled.

#### 24. How did PDF generation work?

**Answer:** I worked on PDF reports containing extensive event details. A complete walkthrough should identify the requested event, authorization, data assembly, PDF library, and how users received the file. PDF generation ran as a Celery task. We populated an HTML template with event contents and converted it to PDF. I use WeasyPrint personally and can explain its implementation, but the historical EventOps renderer is not verified. Generated PDFs were uploaded to S3. I should not attach the separate 16 GB CSV pipeline to this story without evidence.

#### 25. What does 40% to 70% coverage mean?

**Answer:** It is an increase of 30 percentage points, or 75% relative to the original coverage. In interviews I would say “from 40% to 70%” to avoid ambiguity. I improved the pytest framework, used mocking, and expanded important-area tests. I should also explain the measured scope and one meaningful regression case, because coverage alone does not establish correctness.

#### 26. How did you manage transactions after splitting services?

**Answer:** The backend services used a common PostgreSQL database, so I should discuss the actual table/write ownership and migration coupling. A common database does not automatically make writes from separate service requests one atomic transaction. I need to recall the real transaction boundaries. Outbox patterns or compensation are possible designs, not confirmed EventOps features.

## Actual load-testing regression: eager prefetch delayed initial loading

### Interview-ready answer

“I added Django `prefetch_related()` to reduce database calls, expecting faster loading. Load testing exposed roughly a 10-second loading delay. I fixed it by removing prefetch from the initial load and fetching the extra data conditionally in a subsequent call. This resolved the loading issue and kept optional work off the initial critical path, at the cost of another call when needed. Fewer database calls did not necessarily mean a faster user experience.”

### Mechanism and tradeoff

`prefetch_related()` performs additional queries and associates related objects in Python. It helps when those objects are needed, but optional or excessive eager work can delay the initial response. Conditional fetching trades a shorter initial path for a later request and its own loading/error state. Removing prefetch while still reading every related object can introduce repeated per-item queries; a batched conditional fetch is a different choice. See [Django prefetch behavior](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#prefetch-related).

### Scope and follow-ups

Merin owned both the original change and fix; the approximately 10-second delay occurred in load testing. The screen, relation, load-test setup, dominant cost, query counts, and after-fix timing remain unspecified. Production exposure and a specific N+1 diagnosis are not established.

**Proposed regression checks:** the initial path skips optional work; the later fetch retains authorization/tenant scope; its failure leaves initial data usable; representative relationship sizes remain bounded; query count and latency are measured separately; the UI handles changes between responses.

## Production-incident practice scenarios

**These are hypothetical scenarios based on the EventOps stack, not incidents Merin has confirmed.** They are useful for recognizing similar experience and practicing troubleshooting. Use “I would” for a design exercise; use “I did” only for actions actually performed. No incident below is attributed to Amazon, Under Armour, or another client.

Scale can mean bursty demand, concurrent writes, many tenants, large reports, or cascading dependencies. A strong incident answer identifies the affected workflow, diagnoses the mechanism, contains impact, changes the underlying behavior, and demonstrates recovery. It does not need an invented customer count or dramatic outage.

### Choosing the strongest story

| Scenario | Engineering strength demonstrated | Match to confirmed work |
|---|---|---|
| PDF backlog delays other tasks | Capacity reasoning, workload isolation, memory and database limits | Strong: Celery PDF reports, HTML templates |
| Availability endpoint degrades under demand | Query diagnosis, shared-database contention, bounded concurrency | Strong: scheduling, common PostgreSQL |
| Concurrent requests double-book a resource | Transaction correctness and concurrency | Strong: space/equipment scheduling domain |
| Duplicate periodic work after deployment | Distributed scheduling, occurrence identity, safe recovery | Strong: Celery Beat |
| One unavailable service causes cascading failures | Dependency budgets, retry safety, operational diagnosis | Conditional: REST communication tentatively recalled |
| Background task uses the wrong tenant context | Isolation, worker lifecycle, targeted regression testing | Conditional: Django tenancy confirmed; schema mechanism tentative |

The actual prefetch regression above is the primary performance story, detected during load testing rather than a confirmed production incident. The first three hypothetical scenarios are useful for additional scale discussion. Choose one matching a remembered issue rather than memorizing a fictional incident.

### Scenario 1: PDF bursts exhaust worker capacity

**Mechanism:** Reports require data loading, HTML construction, and rendering. If long tasks share workers with shorter work, reports can occupy execution slots and delay everything else. Increasing worker processes can also multiply memory usage and database demand.

**Example:** After a busy event period, many reports are requested close together. Reports remain pending, and any short periodic work sharing those workers becomes late. This is a hypothetical burst, not an observed EventOps incident.

**Tradeoff:** Dedicated queues and worker pools protect short work, but reserve capacity and require task routing. Extra workers help only while memory, CPU, and PostgreSQL can support them. Reusing a completed report is safe only when its data version, permissions, and freshness requirements permit it.

**Failure and response:**

1. Separate queue waiting time from actual render duration. Check active task types, worker restarts, peak memory, and database load.
2. Contain the backlog by limiting report admission/concurrency while preserving urgent work. Avoid automatically adding processes to an already memory-starved host.
3. If resource competition is established, route reports to bounded dedicated workers, reduce repeated data loading, and control task prefetch where it affects long-task distribution.
4. Add a representative burst test with realistic long reports; verify short work remains responsive and report throughput meets demand. Inspect timeouts and clean up partial outputs.

**Evidence:** Task enqueue/start/finish timestamps, oldest waiting-task age by class, render duration, process/container memory, worker exits, and database connection use. None of these measurements is supplied for EventOps. [Celery optimization guidance](https://docs.celeryq.dev/en/stable/userguide/optimizing.html) supports reasoning about queue capacity and workload tuning.

**Illustrative capacity calculation:** with four execution slots and a mean render time of 20 seconds, the idealized ceiling is `4 × 60 / 20 = 12 reports/minute`. At 18 arrivals/minute, backlog grows by about six reports/minute. Real capacity is lower or more variable when resources contend; these are invented calculation inputs, not project metrics.

**Practice answer:** “I would first distinguish waiting time from execution time. If reports were occupying shared workers, I would protect short tasks and bound report concurrency, then check memory and database capacity before scaling. I would prove improvement with queue-age and completion-time measurements under the same workload.”

### Scenario 2: Scheduling becomes slow because of database work

**Mechanism:** Repeated availability queries can create excessive round trips, broad scans, or lock waits. A common database allows reporting and other services to compete with scheduling for connections and resources. Similar symptoms can have different causes; high latency alone does not identify a missing index.

**Example:** An event with several participants and resources triggers one availability lookup per entity, followed by more queries for related details. During concurrent report activity, scheduling slows. The query pattern and contention are hypothetical.

**Tradeoff:** Batch queries can reduce round trips, and appropriate indexes can improve selective reads, but larger joins and indexes have costs. Extra worker connections can worsen database contention. Cached availability may accelerate reads while introducing freshness problems for booking decisions.

**Failure and response:**

1. Trace a slow request and count queries. Distinguish time waiting for a connection, executing queries, waiting on locks, and calling another service.
2. Inspect representative query plans and lock/blocking information. Run expensive analysis against safe representative data or within controlled production limits.
3. Contain competing workload if established; then batch lookups, remove redundant reads, or add a query-appropriate index based on evidence.
4. Compare the same event shapes before and after. Check correctness, database write overhead, and larger tenant data sets as well as median latency.

**Evidence:** Query count per request, query plans, rows examined/returned, blocking sessions, connection counts, and p95/p99 scheduling latency. The exact EventOps ORM access and indexes are unknown. [PostgreSQL locking documentation](https://www.postgresql.org/docs/current/explicit-locking.html) explains locking and inspection facilities; actual query optimization requires the real query and plan.

**Practice answer:** “I would trace the scheduling request before changing capacity. If repeated queries were the cause, I would reduce round trips and verify the relevant plan. If lock or connection contention dominated instead, I would address that mechanism. The outcome would be demonstrated with comparable latency and database-load measurements.”

### Scenario 3: Two concurrent requests reserve the same space

**Mechanism:** Two requests both check availability before either reservation commits. Both see a free interval and insert overlapping bookings. This is a check-then-write race; it can occur without very high traffic.

**Example:** Two planners select the same room and overlapping times. Each succeeds independently, but the combined state violates the booking rule. For quantity-based equipment, the invariant may instead be that total reserved quantity never exceeds inventory.

**Tradeoff:** Serialization protects correctness but adds waiting under contention. Locking a whole resource is simple but coarse; database interval constraints can express some invariants more directly but require suitable schema support. Equipment quantities and interval overlaps need different constraint designs.

**Failure and response:**

1. Confirm overlapping committed reservations and reconstruct request timing; distinguish a race from stale UI data or timezone conversion.
2. Reconcile affected bookings with the responsible operations team; stop silent confirmations if correctness cannot be guaranteed.
3. For a reference fix, lock a stable resource record within a transaction, recheck overlaps, and persist before releasing it. Every competing writer must follow the protocol. Locking existing booking rows alone does not protect a previously empty interval.
4. For multiple resources, acquire locks in a consistent order to limit deadlocks. Keep external calendar/HTTP calls outside long-held database locks where possible, while preserving the final authoritative validation.
5. Use concurrent database connections in a regression test. Assert that conflicting requests cannot both succeed. Also test adjacent intervals and unrelated resources.

**Evidence:** Reproduced interleaving before the fix, rejection of the conflicting transaction after it, no overlapping committed bookings, and acceptable lock-wait latency. Mocked tests alone do not demonstrate database concurrency correctness. [PostgreSQL locking reference](https://www.postgresql.org/docs/current/explicit-locking.html).

**Practice answer:** “The important distinction is that an availability check is not a reservation. I would protect the final check-and-write operation, make all writers follow the same protocol, and test the competing transactions concurrently. I would then measure contention as well as correctness.”

### Scenario 4: Duplicate periodic work after a deployment

**Mechanism:** Two Beat instances owning the same schedule can publish duplicate tasks. Independently, a task that runs longer than its interval can overlap with its next occurrence. Retries or redelivery are separate duplication paths.

**Example:** During deployment, an old scheduler remains active while a new one starts. A periodic workflow executes twice or generates duplicate follow-up work. This is hypothetical; duplicate notifications do not by themselves prove duplicate Beat processes.

**Tradeoff:** Single scheduler ownership is operationally simpler but needs a defined failover process. Occurrence deduplication protects effects but needs persistent identity and cleanup. A permanent “already processed” flag can incorrectly suppress the next legitimate occurrence.

**Failure and response:**

1. Distinguish duplicate publication from repeated worker execution using task IDs, schedule entries, logical occurrence IDs, and process/deployment records.
2. Stop unintended duplicate schedule ownership and pause unsafe replay. Reconcile any repeated business effects.
3. Define one logical occurrence, such as tenant + rule + target + scheduled time/version, and make its execution safe to repeat. Prevent overlap separately where required.
4. Test deployment overlap, failover, retry, and repeated legitimate occurrences. Verify that the fix does not simply drop future work.

**Evidence:** Active scheduler ownership, enqueue and execution records, duplicate business-effect counts, and successful future occurrences. Beat use is confirmed; this incident and its fixes are not. [Celery periodic task guidance](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html).

### Scenario 5: A slow internal service triggers cascading timeouts

**Mechanism:** A scheduling request waits for a slow downstream dependency. Concurrent waits occupy request-handling capacity, while layered retries amplify load. Nginx gateway errors may be the visible symptom rather than the original fault.

**Example:** A resource lookup slows, scheduling waits, and clients retry. Increasing the Nginx timeout hides failures longer but does not increase downstream capacity. Inter-service REST is a tentative recollection; this dependency graph is illustrative.

**Tradeoff:** Short deadlines protect capacity but fail some requests that could eventually succeed. Retries help transient errors but may overload the dependency. A stale fallback may be acceptable for display but unsafe for confirming availability.

**Failure and response:** Correlate request timing across proxy, caller, and downstream service. Contain load and unnecessary retries, then identify whether downstream code, database work, or saturation caused the delay. Apply bounded request budgets and concurrency, and use selective retries only when safe. Validate write outcomes before replay after ambiguous timeouts.

**Evidence:** A correlated slow request, dependency latency, request-slot/concurrency use, retry counts, gateway errors, and recovery under controlled dependency slowdown. Do not claim that circuit breakers, distributed tracing, or replica balancing were implemented without recollection.

### Scenario 6: Background worker retains the previous tenant's context

**Mechanism:** A reused process or database connection may retain tenant state if context is not selected and restored for each task. Request middleware does not automatically run around a background task.

**Example:** A PDF task succeeds in isolation but, after another customer's task, loads incorrect or missing data. This is a hypothetical isolation defect; no actual cross-tenant exposure has been reported. The schema-specific explanation applies only if schema tenancy is confirmed.

**Tradeoff:** Context-managed cleanup supports connection reuse, but implicit process-global state is difficult to reason about. Separate tenant databases/processes would add operational cost and are not automatically the required solution.

**Failure and response:** Suspend affected output delivery, preserve enough evidence to assess scope, and follow the real incident process if incorrect data may have been exposed. Reproduce A → B → A tasks on the same worker/connection, including an exception path. Select tenant context from validated task identity and restore it in guaranteed cleanup. Recheck authorization when delivering reports.

**Evidence:** Tenant-scoped test data, sequential mixed-tenant reproduction, exception cleanup assertions, and no cross-tenant reads after the fix. Django multi-tenancy is confirmed; task context leaks, the tenancy package, and schema-level isolation are not.
