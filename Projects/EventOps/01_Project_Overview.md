# EventOps — project overview, stack and contributions

**InApp | September 2019-November 2021 | Merin Rose Tom**

[Interview questions and answers](05_Interview_QA.md)


---

## Technology stack

| Layer | Technology | Role |
|---|---|---|
| Frontend | Angular, JavaScript | Event-management screens, visualizations, authentication-related UI, user interactions |
| Original backend | Python, Django | Original monolithic application and backend functionality |
| Extracted backend services | Python, Flask | Microservices introduced during the migration |
| Persistence | PostgreSQL | Common database used by backend services |
| Database access | Django ORM, `Q`, `F` | Main query mechanism; complex predicates and database-side field expressions |
| Hosting | Amazon EC2 | Application hosting |
| Report storage | Amazon S3 | Uploaded generated PDF reports |
| Background execution | Celery | Asynchronous work, including PDF report generation |
| Periodic scheduling | Celery Beat | Periodic work including upcoming-event reminders |
| Email delivery | SendGrid | Send automated email notifications |
| Authentication / authorization | Django auth, SSO, manual login, backend decorators | Two login options and admin-specific API protection |
| Calendar integration | Out-of-office source | Used for availability checks; API/provider and relation to SSO unverified |
| Tenant architecture | Django multi-tenancy | Multi-tenant application; exact package and schema mechanism unverified |
| Background infrastructure | Redis | Used with Celery; exact broker/result-backend configuration not recalled |
| Containers | Docker, Docker Compose | Separate image per service; YAML-based multi-container startup and networking |
| Traffic routing | Nginx | Routing requests to backend components |
| Unit testing | pytest, mocking | Isolated tests and improved important-area coverage |
| Reporting template | HTML populated with event contents | Reusable report structure separated from event-specific data |
| PDF walkthrough | WeasyPrint | Concrete implementation example based on Merin's personal use; historical EventOps renderer unverified |

Celery Beat handled periodic scheduling and SendGrid handled email sending. Django authentication and decorator-protected admin APIs are confirmed. Amazon EC2 hosted the app, with separate Docker images per service. Precise authentication/session settings, framework versions, image registry, and CI/CD configuration remain unspecified. Docker use alone does not identify a container orchestrator.


---

## Product purpose and scope

EventOps managed organizational event operations involving spaces, equipment, people, budgeting, and reporting. It combined event planning with workflow automation, reducing repeated coordination and manual follow-up.

**Notable clients:** Amazon and Under Armour, as recalled by Merin.

| Capability | Purpose |
|---|---|
| User management | Maintain users and support role-based access |
| Space management | Maintain spaces and modify their availability |
| Equipment management | Maintain equipment and modify its availability |
| User availability | Modify user availability and support calendar-based scheduling checks |
| Event management | Organize event information and associated space/equipment requirements |
| Participant scheduling | Check availability using an out-of-office calendar |
| Conditional task generation | Create work when relevant business conditions are met |
| Automated email | Communicate workflow updates and required actions |
| Role-based access control | Regulate operations for different user types |
| PDF reporting | Produce detailed event documents from populated HTML templates |
| Frontend dashboards/components | Present information and support user interactions |

Merin worked on the project across trainee and software-engineer roles at InApp. The latest confirmed project dates are **September 2019-November 2021**. The older portfolio excerpt displays July 2019-June 2020; this guide uses the direct correction.

The [official EventOPS website](https://eventops.com/) supplies current product context. Historical implementation details in this guide come from Merin and the supplied career materials.


---

## Conceptual data model

The following entities explain the domain. They are reference names, not recovered production tables.

| Entity | Purpose | Relationship |
|---|---|---|
| Tenant / organization | Customer boundary | Contains customer-scoped event data |
| User membership | User's organization and permissions | Connects users to an authorized scope |
| Event | Main event details and lifecycle | Associated with participants and operational requirements |
| Space | Event space and its availability | Resource available to event planning |
| Equipment | Event equipment and its availability | Resource available to event planning |
| Availability entry | User, space, or equipment availability information | Updated through the corresponding management capability; user scheduling also checks the out-of-office calendar |
| Task | Assigned work | Associated with an event and responsible user |
| Automation rule | Trigger, condition, action | Determines conditional workflow behavior |
| Report request / execution | PDF-generation work and outcome | Reference entity for background reporting; persistence unverified |

Query patterns determine useful indexes. Examples include event lists by status/date, participant availability over a time range, and due work by state/time. Actual indexes and query plans have not been supplied.


---

## My contributions

### Backend modernization

I was a main contributor to moving the original Django monolith toward Flask-based microservices, using Docker for services and Nginx for routing. The confirmed contribution concerns migration and modularization; exact extracted capabilities and rollout responsibilities remain to be documented.

### Scheduling and workflow automation

I worked on scheduling that checked participant availability from an out-of-office calendar, automated email notifications, and rule-based workflows. These capabilities reduced repeated coordination and supported more consistent event operations.

### Detailed event reports

I worked on PDF generation executed through Celery. Reports used an HTML template populated with event contents before conversion to PDF. WeasyPrint provides the concrete technical walkthrough in this guide based on my personal use.

### Testing framework improvements

Initial unit test coverage was approximately 40%. I developed and improved the pytest-based unit testing framework, expanded coverage over important areas, and used mocking to isolate dependencies. Coverage reached 70%, a **30 percentage-point increase**.

### Frontend and access control

The portfolio records Angular components supporting visualizations, authentication-related interactions, and user workflows, alongside role-based access improvements. Specific screens and role definitions remain unspecified.


---

## Testing approach and results

The confirmed testing work used pytest and mocking; the portfolio also identifies Django multi-tenancy testing. Coverage improved from 40% to 70%. The exact measured code scope and whether the metric was line or branch coverage remain unknown.

Mocking isolates dependencies so business behavior can be exercised without every external component. For example, a reference notification unit test can replace an email adapter, execute a qualifying condition, and assert the intended action. A nonqualifying condition should make no delivery call. These are illustrative cases, not a claim that particular tests were written.

| Test area | Representative coverage |
|---|---|
| Workflow conditions | Matching/nonmatching condition, disabled rule, unrelated update |
| Scheduling | Absence overlap, boundary times, rescheduling, invalid duration |
| Permissions | Authorized operation, denied operation, object-level restriction |
| Tenancy | Customer isolation and context cleanup |
| PDF reporting | Template population, missing optional fields, rendering failure |
| Background work | Failure handling, duplicate execution, cancelled/stale work |

The table is a proposed coverage map; individual cases require confirmation. Unit tests, database/request integration tests, worker integration, and browser tests provide different evidence. Mocked unit tests alone do not establish real queue delivery or browser behavior. See [Django testing tools](https://docs.djangoproject.com/en/5.2/topics/testing/tools/).


---

## Implementation notes and sources

Confirmed details and clearly labeled reference explanations are kept separate. Remaining unknowns are the exact deployed service boundaries/names, table/write ownership, inter-service REST details (tentative recollection), tenancy package/context selection, calendar integration, Beat schedule configuration, historical renderer/template engine, SendGrid integration method, EC2/VPC topology, security-group rules, exact Compose YAML/image registry/S3 access configuration, exact auth/decorator configuration and identity propagation, rollout, and exact coverage scope. No private EventOps source code has been inspected.

The 16 GB CSV pipeline, shared LRU cache, piracy analytics, and Oracle/OCI work are not attributed to EventOps without evidence.

Sources:

- Merin's direct clarifications: corrected dates, stack, common database, confirmed Django multi-tenancy with tentative schema isolation, SendGrid, Celery Beat and upcoming-event reminders, SSO/manual login, Nginx mainly for routing, tentative inter-service REST recollection, migration driven by feature complexity/regressions/testing difficulty, Django auth and admin API decorators, SSO-associated calendar access, migration contribution, out-of-office scheduling, Celery PDF tasks and S3 uploads, Django ORM with Q/F expressions, EC2 hosting and per-service Docker images/builds, populated HTML templates, personal WeasyPrint use, pytest/mocking, and 40%-70% coverage.
- Resume and LinkedIn export: role history, EventOps capabilities, recognition, and career statements.
- Supplied [portfolio](https://merinrose123.github.io/merin-rose-tom/) excerpt: product scope, architecture, frontend, testing, workflows, RBAC, and approximate outcomes. Direct website retrieval was unavailable; the supplied text was used.
- [Official EventOPS website](https://eventops.com/): public product context, accessed 28 October 2026.
- Framework documentation linked within the relevant technical sections supports reference explanations; it does not establish historical versions or implementation.

