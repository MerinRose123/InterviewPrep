# EventOps: project architecture, implementation, and contributions

**InApp | September 2019-November 2021 | Merin Rose Tom**

[Interview questions and answers](Interview_Questions_and_Answers.md)

## 1. Project architecture

EventOps managed events together with the users, spaces, and equipment needed to run them. Users could modify availability, schedule events, receive email notifications, and generate detailed PDF reports. The application evolved from a Django monolith toward Flask-based microservices, with Angular in the browser, Nginx routing on the backend, Docker-packaged services, and a common PostgreSQL database.

### System architecture

```mermaid
flowchart LR
    subgraph BROWSER[User browser]
        direction TB
        ANGULAR[Angular application]
        SCREENS[EventOps UI]
        SCREENS --- ANGULAR
    end

    subgraph SERVER[Amazon EC2 - application hosting]
        direction TB
        NGINX[Nginx]

        subgraph SERVICES[Python microservices - Docker]
            direction TB
            USERS[Users]
            SPACE[Spaces]
            EQUIP[Equipment]
            SCHEDULE[Scheduling]
            WORKFLOW[Workflows]
            NOTIFY[Notifications]
            REPORT[Reports]
        end

        NGINX --> USERS
        NGINX --> SPACE
        NGINX --> EQUIP
        NGINX --> SCHEDULE
        NGINX --> WORKFLOW
        NGINX --> NOTIFY
        NGINX --> REPORT

        DATA[Django ORM]
        USERS --> DATA
        SPACE --> DATA
        EQUIP --> DATA
        SCHEDULE --> DATA
        WORKFLOW --> DATA
        NOTIFY -.-> DATA
        REPORT --> DATA

        subgraph BACKGROUND[Background processing]
            REDIS[Redis]
            CELERY[Celery workers]
            PDF[HTML to PDF]
            REDIS -.-> CELERY
            BEAT[Celery Beat] -->|Periodic tasks| CELERY
            CELERY --> PDF
        end
        REPORT -->|PDF task| CELERY
        CELERY --> DATA
        WORKFLOW -.-> NOTIFY
    end

    subgraph DATABASE[Database boundary]
        PG[(PostgreSQL)]
        TENANT[Django multi-tenancy]
        PG --- TENANT
    end

    CAL[Out-of-office calendar]
    MAIL[SendGrid]
    S3[(Amazon S3 - PDFs)]
    PDF --> S3

    ANGULAR -->|HTTP API| NGINX
    DATA --> PG
    SCHEDULE --> CAL
    NOTIFY --> MAIL

    classDef frontend fill:#dbeafe,stroke:#2563eb,color:#172554;
    classDef gateway fill:#ffedd5,stroke:#ea580c,color:#431407;
    classDef service fill:#e0e7ff,stroke:#6366f1,color:#1e1b4b;
    classDef database fill:#dcfce7,stroke:#16a34a,color:#052e16;
    classDef background fill:#f3e8ff,stroke:#9333ea,color:#3b0764;
    class ANGULAR,SCREENS frontend;
    class NGINX gateway;
    class USERS,SPACE,EQUIP,SCHEDULE,WORKFLOW,NOTIFY,REPORT service;
    class PG,TENANT database;
    class REDIS,CELERY,BEAT,PDF background;
```

**Reading the diagram:** the browser contains Angular; the server contains Nginx, backend services, and background processing; PostgreSQL is shown as a separate database boundary. The server box groups backend responsibilities and does not assert that every component ran on one physical machine. The ORM box summarizes database access; it is not a separate deployed service. Django ORM was the main access mechanism, but the exact integration used by each Flask service remains unknown. EC2 hosting is confirmed; PostgreSQL placement and the number of EC2 instances are not.

**Reconstruction scope:** user, space, equipment, availability, scheduling, email, and reporting capabilities are confirmed. They are shown as functional microservice boundaries to explain the architecture requested here. Their exact original deployment names, specific deployed service names and split between Django and Flask remain unverified. A separate Docker image per service is confirmed. Workflow and notification connections shown with dotted lines are illustrative. SendGrid email delivery, Django multi-tenancy, and Celery Beat periodic scheduling are confirmed. Redis's exact role and schema-level isolation remain uncertain. The calendar provider is unspecified.

### Service responsibilities and routing

The route prefixes below illustrate Nginx routing; they are not recovered production URLs.

| Service | Responsibility | Availability / data handled | Illustrative route |
|---|---|---|---|
| User management | Maintain users and role-related operations | User details and user availability modifications | `/api/users/` |
| Space management | Maintain event spaces and their availability | Space details and availability modifications | `/api/spaces/` |
| Equipment management | Maintain event equipment and its availability | Equipment details and availability modifications | `/api/equipment/` |
| Event and scheduling | Manage event scheduling and relevant resource allocation | Event timing, participants, space/equipment requirements; out-of-office checks | `/api/events/`, `/api/scheduling/` |
| Workflow | Apply conditions and generate follow-up tasks | Triggers, conditions, task assignments | `/api/workflows/` |
| Notifications | Prepare and send event-related email | Recipient and notification content; persistence unspecified | `/api/notifications/` |
| Reporting | Accept event report requests and dispatch PDF work | Event report inputs and HTML-template content | `/api/reports/` |

Availability modifications belong with the entity being managed: user availability with users, space availability with spaces, and equipment availability with equipment. Scheduling consumes the relevant availability information. The historical mechanism for obtaining resource availability across service boundaries is not yet recalled; the shared database does not establish whether scheduling queried tables directly or called service APIs.

### Request and background execution paths

A space-availability update starts in Angular, reaches Nginx, and is routed to the space capability. The backend validates the request and permissions, updates the relevant PostgreSQL data, and returns the result to the browser. This is a reconstructed request path using the confirmed technology stack; actual endpoints and permission middleware remain unspecified. Equipment and user availability follow the same responsibility model.

Scheduling combines the proposed event timing and relevant availability data. Participant availability came from an out-of-office calendar. Space and equipment availability were also managed, but the exact rules for combining all three availability sources in one scheduling decision remain to be recalled.

Reporting uses a different execution path: the reporting capability dispatches PDF generation as a Celery task; the task populates an HTML template with event contents and renders the PDF. The generation mechanism is confirmed, while PDF upload to an S3 bucket is confirmed; job-status tracking, object naming, and authorized download delivery remain unspecified.

### Evolution from the original monolith

```mermaid
flowchart LR
    subgraph BEFORE[Before - Django monolith]
        D[Django application<br/>Users / Spaces / Equipment<br/>Events / Workflows / Reports]
    end
    subgraph AFTER[After - backend service boundaries]
        N[Nginx routing]
        U[Users]
        S[Spaces]
        E[Equipment]
        EV[Events / Scheduling]
        W[Workflows / Notifications]
        R[Reporting]
        N --> U
        N --> S
        N --> E
        N --> EV
        N --> W
        N --> R
    end
    D -. extraction into Flask-based services .-> N
```

The migration changed application boundaries while retaining a common database. This supported modular development but preserved database coupling: schema changes and competing writes could still affect multiple services. The capability grouping above is a reconstruction, not a verified extraction sequence.

Tenant isolation was probably implemented through separate PostgreSQL schemas within the common database. Customer isolation and service ownership are separate concerns: tenant schemas would separate customers, while services could still share the same customer's data.

## 2. Technology stack

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
| Containers | Docker | Separate image per service; image builds and container deployment |
| Traffic routing | Nginx | Routing requests to backend components |
| Unit testing | pytest, mocking | Isolated tests and improved important-area coverage |
| Reporting template | HTML populated with event contents | Reusable report structure separated from event-specific data |
| PDF walkthrough | WeasyPrint | Concrete implementation example based on Merin's personal use; historical EventOps renderer unverified |

Celery Beat handled periodic scheduling and SendGrid handled email sending. Django authentication and decorator-protected admin APIs are confirmed. Amazon EC2 hosted the app, with separate Docker images per service. Precise authentication/session settings, framework versions, image registry, and CI/CD configuration remain unspecified. Docker use alone does not identify a container orchestrator.

## 3. Product purpose and scope

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

## 4. Backend migration: Django monolith to Flask services

Merin was a main contributor to converting the original Django application toward Flask-based microservices. Docker supported service packaging and Nginx mainly provided routing. The immediate drivers were increasing feature-management complexity, changes introducing regressions in other areas, and growing difficulty testing the application. Individual extracted service names and the rollout sequence remain to be recalled.

### Why the monolith was split

As EventOps accumulated user, space, equipment, availability, workflow, notification, and reporting features, managing them within one application became difficult. Changes in one area introduced regressions elsewhere, and testing became harder because changes had a wider impact. These are the confirmed reasons for moving toward smaller service boundaries.

| Observed problem | Intended architectural response | Important limit |
|---|---|---|
| Too many features to manage together | Group functionality behind clearer capability boundaries | Separate processes do not automatically remove code/data coupling |
| Changes caused regressions in other areas | Make interfaces and responsibilities explicit, reducing unintended cross-feature changes | Shared PostgreSQL schema changes can still affect several services |
| Testing became difficult | Test bounded service behavior and its contracts more directly | End-to-end and integration testing become more important across services |

Additional possible benefits include clearer ownership, smaller release units, easier fault localization, and workload-specific deployment or scaling. These are reasonable motivations to discuss, not confirmed EventOps outcomes. Independent releases or scaling require supporting deployment and data boundaries; they do not follow from Flask or Docker alone.

The tradeoff was additional network communication, configuration, service integration, and failure handling. A modular monolith was another possible response to feature coupling. The migration is best explained as an engineering choice made to manage growing complexity, not a claim that microservices always outperform monoliths.

### Application boundaries and contracts

A monolith can call internal modules directly and coordinate work inside one application. Extracted services introduce explicit interfaces and network boundaries. Request data, response formats, validation, authorization, and error behavior become part of the contract between the frontend and backend components.

Django and Flask are frameworks rather than architecture categories. Flask supports lightweight service construction, but is not inherently more scalable than Django. The architectural change was the separation of capabilities and routing, not simply a framework substitution.

### Common database and coordination

The backend services used a common PostgreSQL database. Exact shared tables and write ownership remain unknown. A common database simplifies access to existing data during extraction but couples services through schema and transaction behavior. Two separate requests using the same database are not automatically one atomic transaction.

### Packaging and routing

Docker packaged service code with its runtime dependencies. Nginx mainly routed incoming requests to different backend components; replica load balancing is not a confirmed EventOps use. Authentication and permission checks still belonged in the application or an explicitly configured identity layer; routing alone did not establish user authorization.

### Inter-service communication

Nginx primarily routed frontend requests to the appropriate service. Merin tentatively recalls REST calls for inter-service communication. These are different paths: a browser request reaching a service through Nginx does not establish that every internal call also passed through Nginx.

Synchronous REST lets a service obtain an immediate answer from another capability, at the cost of network latency and dependency failures. Celery supported work that could execute later, including PDF generation. The exact internal HTTP endpoints, clients, authentication propagation, tenant propagation, and timeout/retry settings remain unverified. The shared database is confirmed, but direct access by one service to another capability's tables is not established.

### Migration mechanics: reference explanation

A gradual extraction can preserve existing behavior while moving a bounded capability to a separate service: characterize the existing workflow, define its contract, implement the service, verify behavior and permissions, and change the relevant route. This is a reference migration method; the exact EventOps extraction order and rollout strategy have not been established. Routing rollback also requires database compatibility to be effective.

## 5. Event scheduling and participant availability

Event scheduling used an **out-of-office calendar** to check participant availability. This establishes absence-based availability checking, rather than necessarily a complete meeting-calendar free/busy integration. SSO was used for application login, alongside manual login; the exact mechanism used to retrieve calendar data is not currently remembered. The identity/calendar provider, SSO protocol, calendar-access API, permissions/scopes, and representation of availability remain unverified. SSO establishes identity; the data integration still needs appropriate authorization to read calendar information.

```mermaid
flowchart LR
    E[Proposed event time and participants] --> C[Check out-of-office calendar]
    C --> V[Evaluate participant availability]
    V --> RESULT[Scheduling outcome]
```

The confirmed workflow checked availability. Whether it searched for alternative slots or validated a selected slot is not yet known.

### Interval overlap: reference algorithm

For half-open intervals `[start, end)`, a calendar interval overlaps a proposed event when:

```text
calendar_start < event_end AND calendar_end > event_start
```

For example, an absence from 10:00 to 12:00 conflicts with an event from 11:00 to 11:30, while an event beginning at 12:00 is adjacent under this convention. All-day absences and time zones require explicit interpretation. This algorithm is a reference explanation, not recovered EventOps code.

### Concurrent scheduling

An availability query followed by an unprotected save can race with another request. A reference booking design serializes conflicting decisions and rechecks relevant constraints inside the protected operation. A unique start-time constraint alone cannot prevent arbitrary interval overlap. The actual EventOps concurrency mechanism remains unknown.

## 6. Conditional workflows and email notifications

EventOps included rule-based triggers, conditional task generation, and automated email notifications. Merin contributed to these automation capabilities and access controls.

| Workflow element | Responsibility | Illustrative example |
|---|---|---|
| Trigger | Identify a business occurrence | Event enters an approved state |
| Condition | Determine whether action is applicable | A planner has been assigned |
| Action | Perform business work | Create an assigned follow-up task |
| Notification | Communicate the result | Email the responsible person |

The example illustrates the model; it is not a recalled EventOps rule. SendGrid sent the emails. The real rule format, configuration mechanism, recipients, and SendGrid API/SMTP integration details remain unspecified.

SendGrid provided email delivery. The notification capability prepared the message and handed it to SendGrid; whether the integration used its HTTP API or SMTP, and whether delivery webhooks were tracked, remain unspecified.

Business state changes, task generation, and email delivery have different failure boundaries. An email failure need not undo an already-created business task. Retrying notification delivery should not recreate business work unintentionally.

### Transaction and delivery reliability: reference design

For Django code, dispatching through `transaction.on_commit()` can prevent a worker from observing a change that subsequently rolls back. It does not eliminate the crash window between commit and publication. A transactional outbox is one stronger approach to durable dispatch, but is not a confirmed EventOps feature. See [Django transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).

Repeated execution requires an identity for each logical action occurrence and safe state transitions. Exactly-once external email delivery cannot be inferred from a local completion flag: a provider may accept an email before the worker records success. The historical retry/deduplication mechanisms remain unknown.

## 7. Background processing with Celery and Redis

Celery and Redis supported background processing, and Celery Beat scheduled periodic tasks. PDF generation is a confirmed Celery workload. The assignment of email work to Celery, Redis's exact role, retry settings, and acknowledgment settings have not been recalled.

Background execution separates request handling from slower work. It introduces queue waiting time, worker execution time, and a later success/failure outcome. Celery relocates work; it does not make the PDF renderer intrinsically faster.

Celery Beat determined when periodic work became due and dispatched it for Celery workers to execute. Beat was the scheduler; workers performed the work. A broker carries tasks, while a result backend can store task outcomes. Upcoming-event reminders are a confirmed periodic use case. The exact Redis role, schedule storage, reminder interval, and other periodic tasks remain unspecified. See the [Celery task guide](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

### Periodic example: upcoming-event reminders

Upcoming-event reminders were part of EventOps periodic processing. Beat scheduled periodic work, Celery workers executed it, and SendGrid provided email delivery. The exact reminder lead time, scan interval, and task decomposition remain unverified.

A reference implementation scans for reminders that are due, rechecks that the associated event is still eligible, and dispatches the notification. It records a logical reminder occurrence to support safe retries. This scan/deduplication design illustrates the confirmed feature; the historical query, status fields, and duplicate-prevention method are not recalled. Cancellation, rescheduling, time zones, and overdue work after downtime are useful test cases.

## 8. Detailed event PDF reporting

Merin worked on PDF reports containing extensive event details. Generation ran as a **Celery task**. Event contents were added by formatting/populating an **HTML template**, and the populated HTML was converted to PDF.

```mermaid
flowchart LR
    TASK[Celery report task] --> DATA[Event report contents]
    DATA --> TEMPLATE[Populate HTML template]
    TEMPLATE --> RENDER[HTML-to-PDF conversion]
    RENDER --> PDF[Detailed event PDF]
    PDF --> S3[(Amazon S3 bucket)]
```

The template separated stable report structure from variable event content. Stable structure can include headings, tables, branding, and print styles. Variable content contains the selected event's fields and detail rows. Generated PDFs were uploaded to an Amazon S3 bucket. Exact report fields, template formatting API, object naming, and download delivery remain unverified.

### WeasyPrint implementation walkthrough

WeasyPrint is the chosen implementation example because Merin uses it personally. The historical EventOps renderer remains unverified; the earlier pdfkit recollection was tentative.

In this reference implementation, scoped event data becomes a presentation context, a template engine produces HTML, and WeasyPrint converts that HTML into PDF bytes. A controlled base URL resolves relative stylesheets, fonts, and images.

```python
from weasyprint import HTML


def render_event_pdf(rendered_html, asset_base_url):
    return HTML(
        string=rendered_html,
        base_url=asset_base_url,
    ).write_pdf()
```

This is the rendering step, not a complete Celery task. With no output target, `write_pdf()` returns PDF bytes. Django templates or Jinja are possible template engines; the historical choice is unknown. The [WeasyPrint documentation](https://doc.courtbouillon.org/weasyprint/latest/first_steps.html) describes the API and setup.

### Template formatting and layout

Formatting an HTML template does not establish use of Python `str.format()` or f-strings. A template engine can provide repetition, conditionals, and escaping. For a reference implementation, ordinary event text should be escaped appropriately rather than inserted as trusted HTML.

Print styles govern page size, margins, table layout, and pagination. Long tables, missing fonts, image paths, and page breaks are material report-quality concerns. Worker images must include the renderer's version-appropriate dependencies and fonts. Resource fetching and rendering limits matter when inputs or URLs are untrusted. See [WeasyPrint web application considerations](https://doc.courtbouillon.org/weasyprint/stable/common_use_cases.html).

### Report consistency and performance

A report assembled through several queries can combine data from different moments unless the application defines a snapshot strategy. Generation access and later download access are also separate authorization boundaries. These are design considerations; the historical implementation is not yet established.

There is no EventOps benchmark proving a renderer fastest or most memory efficient. WeasyPrint suits HTML/CSS template workflows; ReportLab is an alternative for directly programmed document layout. Representative report size, images, fonts, latency, peak memory, and worker concurrency determine efficiency.

## 9. Persistence, tenant isolation, and access control

### Shared PostgreSQL database

The common database served the backend services. This describes the database boundary, not the exact table ownership or migration process. A service extraction can retain shared data while introducing application-level interfaces, with the tradeoff that schema compatibility still affects several components.

### Database communication through Django ORM

Django ORM was the main mechanism for communicating with PostgreSQL. Application code expressed reads and writes through models and QuerySets rather than primarily hand-written SQL. Merin used `Q` objects and `F` expressions for more complex queries. The exact ORM bootstrap or integration used inside Flask services is not yet recalled; Flask does not provide Django ORM automatically.

`Q` builds composable boolean predicates such as AND, OR, and NOT. `F` refers to database field values within expressions, allowing field comparisons or updates without first loading a value into Python. The following examples illustrate the APIs; model/field names and business conditions are not recovered EventOps code.

```python
from django.db.models import Q, F

# Illustrative OR condition; tenant_queryset is already correctly scoped.
events = tenant_queryset.filter(
    Q(status="planned") | Q(status="confirmed")
)

# Illustrative field-to-field comparison.
over_budget = tenant_queryset.filter(actual_cost__gt=F("budget"))
```

QuerySets are generally evaluated when results are consumed, not when a filter is constructed. ORM use does not eliminate the need to examine generated queries, indexes, transaction boundaries, or relation loading. The actual prefetch load-test regression below is an example of why access patterns matter. See [Django queries](https://docs.djangoproject.com/en/5.2/topics/db/queries/) and [query expressions](https://docs.djangoproject.com/en/5.2/ref/models/expressions/).

### Tentative schema-per-tenant model

EventOps used a Django-based multi-tenant architecture, now confirmed by Merin. The exact package name is not identified. Schema-level tenant separation remains a tentative recollection; if confirmed, the conceptual structure would be:

```text
Common PostgreSQL database
  |-- Tenant A schema: customer-owned tables
  |-- Tenant B schema: customer-owned tables
  |-- Other tenant schemas
```

This is a tentative model, not a recovered schema listing. Schema-per-tenant implementations need controlled tenant selection, context restoration on reused connections, and equivalent context handling in background jobs. Celery does not automatically preserve Django request context. Separate schemas also do not prove database-enforced isolation if one role can access every schema.

### Authentication and authorization

EventOps offered both **SSO login** and a **manual login** mechanism. Django authentication mechanisms were used for application user authentication. Admin-specific APIs were protected with decorators in the backend code. Merin also worked on role-based access control. The exact login/session/token configuration, decorator implementations, and role names have not been identified.

Authentication established the user identity; authorization controlled which API operations that user could perform. An authenticated user was not automatically allowed to invoke admin APIs. Decorators placed checks around protected view functions before privileged logic executed. Whether the project used built-in decorators, custom decorators, or a combination remains unspecified.

A reference authorization sequence is authenticated identity → verified tenant scope → required role/permission → access to the specific object. The tenant/object checks are design requirements to verify, not evidence that a particular decorator implemented all four layers. Backend protection applies even when an unauthorized user calls the API directly rather than through Angular.

Django supports authentication and permission facilities, including view decorators; exact behavior depends on the chosen implementation. See [Django authentication documentation](https://docs.djangoproject.com/en/5.2/topics/auth/default/). A login check alone is not an admin permission check, and a staff flag need not represent a tenant-scoped business-administrator role.

### SSO and out-of-office calendar access

SSO login and manual login were both supported for initial application access. Earlier recollection associated SSO with obtaining out-of-office data, but the exact calendar integration is not remembered. The confirmed scheduling behavior is checking out-of-office availability; SSO login alone does not establish how calendar data was retrieved or how internal service calls were authenticated. The historical identity provider, protocol, API credentials, delegated access, and refresh mechanism remain unknown.

```text
Application login options: SSO or manual login
Application authentication: Django authentication
Admin API access: backend decorator checks
Calendar access: out-of-office source; exact mechanism unverified
Tenant isolation: Django multi-tenancy
```

SSO identifies a user; reading calendar data additionally depends on the integration's granted access. No OAuth/OIDC, SAML, Microsoft/Google integration, or JWT propagation is asserted without confirmation. Failed calendar access should not be treated as proof of participant availability; actual failure behavior remains to be recalled.

UI controls reflect permissions; backend checks enforce them. Reports, exports, related-object access, and background work need the same scope discipline as primary APIs. How Django identity and authorization were validated in the extracted Flask services remains an important unresolved boundary.

### SSO behind the scenes: reference walkthrough

**Confirmed for EventOps:** SSO login and manual login were both available, Django authentication was used, and decorators protected admin APIs. The identity provider, SSO protocol, session backend, and integration package remain unknown. The following server-side OIDC flow explains a possible implementation, not recovered EventOps code.

#### Components and trust

| Component | Responsibility in the reference design |
|---|---|
| Angular / browser | Starts login and follows redirects |
| Nginx | Routes requests to the application; does not itself prove identity |
| Django / SSO integration | Starts authentication, validates the response, maps the identity, establishes application login |
| Identity provider, or IdP | Authenticates the user, potentially with MFA and an existing organizational session |
| Application user and tenant records | Determine EventOps membership, access, and permissions |

SSO means applications trust an identity provider's authenticated result rather than independently asking for the corporate password. Each application can still maintain its own session. The user is not automatically an administrator simply because corporate login succeeded.

#### Visual flow: OIDC authorization code example

```mermaid
sequenceDiagram
    actor User
    participant Browser as Browser / Angular
    participant App as Django via Nginx
    participant IdP as Identity provider
    User->>Browser: Choose SSO
    Browser->>App: Start login
    App-->>Browser: Redirect to IdP with transaction parameters
    Browser->>IdP: Authorization request
    IdP->>User: Login / MFA if required
    User->>IdP: Authenticate
    IdP-->>Browser: Redirect to registered callback with code
    Browser->>App: Callback with code and state
    App->>App: Validate login transaction
    App->>IdP: Exchange code with PKCE verifier and client authentication
    IdP-->>App: ID token and access token
    App->>App: Validate identity and map authorized local user
    App-->>Browser: Set application session cookie and redirect
    Browser->>App: API request with session cookie
    App->>App: Check role, tenant, and object access
```

The arrows describe logical endpoints. Nginx forwards browser requests; the backend's token exchange need not pass through the browser. A server-side client keeps its credentials and provider tokens on the server in this reference design.

#### 1. Start a login transaction

The application redirects the browser to the provider with a client identifier, registered callback, requested scopes, and transaction state. After authentication, the provider returns a short-lived code; the backend exchanges it at the token endpoint. This is the authorization-code pattern, not sending the corporate password to EventOps. See [OAuth 2.0 authorization code flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1).

The browser may already have a valid provider session from another company application. The provider can then complete authentication without another password prompt, subject to its policies. This is the visible “single sign-on” effect; the provider and EventOps still have separate session lifecycles.

#### 2. Bind the callback to the attempted login

`state` correlates the callback with the initiating browser transaction and helps prevent login CSRF. PKCE uses a per-login verifier and a derived challenge; the code exchange must present the verifier. The verifier should not be exposed as the authorization-request challenge. PKCE protects against intercepted-code misuse. See [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636).

An OIDC request can also include `nonce`, which must match the returned ID token when supplied. It binds the identity response to the login transaction. State, nonce, and PKCE serve different checks; none substitutes for validating the provider and token.

#### 3. Validate the identity response

OIDC adds an ID token containing identity claims. Validation includes the signature, expected issuer, audience/client, expiry, and applicable transaction checks. Use the issuer and subject as the external identity key; email alone is not a reliable account-linking key. An ID token identifies a login; an access token authorizes access to its intended resource. See [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html).

Provider metadata can publish authorization/token endpoints and the signing-key location, often exposed as JWKS. Trust comes from the configured issuer, HTTPS, and correct validation—not merely decoding a JWT or following a key URL supplied by an untrusted token. See [OIDC Discovery](https://openid.net/specs/openid-connect-discovery-1_0.html).

#### 4. Establish the local user and application session

The reference backend maps the validated identity to an authorized local user, then uses Django login/session handling. Manual login validates credentials through the configured Django authentication backend. Both paths can converge on the same local permission checks. Actual EventOps provisioning and account-linking behavior are unknown.

For a server-side session design, the browser holds a session identifier cookie; requests resolve it to local identity. HttpOnly restricts JavaScript access, Secure restricts transmission to HTTPS, and cookie-based state-changing requests require CSRF protection. SSO login does not remove those application concerns. See [Django authentication](https://docs.djangoproject.com/en/5.2/topics/auth/default/).

Django's application session is not automatically understood by Flask. Shared session validation, an internal identity check, or appropriately validated access tokens are possible service-boundary mechanisms. The historical mechanism remains unverified.

#### 5. Distinguish application logout from provider logout

Logging out of EventOps should terminate its application session. The provider session may remain active, allowing a later SSO attempt to log in again without a password. Ending the provider session is a separate flow and can affect other applications. [OIDC RP-initiated logout](https://openid.net/specs/openid-connect-rpinitiated-1_0.html) is one modern specification; it became final in 2022 and is not evidence of EventOps' 2019-2021 implementation.

#### SAML: an alternative historical implementation

SAML browser SSO uses an identity assertion, commonly delivered to the application's assertion-consumer endpoint, rather than the OIDC code/token sequence above. The application validates signature, issuer, intended audience, destination, timing, request correlation, and replay protection before creating local login state. Use a maintained integration library. See [OWASP SAML guidance](https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html).

| Memory clue | Possible protocol |
|---|---|
| Authorization/token endpoints, `openid` scope, ID token | OIDC |
| XML metadata, assertion, ACS URL, `SAMLResponse` | SAML |
| A corporate login page or MFA prompt alone | Insufficient to distinguish protocols |

Neither protocol is confirmed for EventOps. Current documentation explains concepts; its latest features and versions are not historical project claims.

## 10. Conceptual data model

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

## 11. My contributions

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

## 12. Testing approach and results

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

## 13. Outcomes and engineering tradeoffs

| Outcome | Evidence and interpretation |
|---|---|
| Load-test regression resolved | Personally added prefetch to reduce DB calls; load testing exposed an approximately 10-second loading delay; personally fixed it with conditional fetching in a later call; after-fix timing unspecified |
| Test coverage: 40% to 70% | Directly confirmed; +30 percentage points, equivalent to 75% relative growth |
| Approximately 20% operational/manual-effort improvement | Career materials; baseline and measurement method remain unspecified |
| Approximately 15% efficiency improvement | Portfolio performance/debugging claim; metric definition remains unspecified |
| CEO appreciation | Documented recognition for EventOps contribution |

The most concrete numerical result is the coverage baseline and final value. The approximate efficiency figures should not be interpreted as API latency, throughput, or cloud-cost improvements without supporting measurement.

| Design choice | Benefit | Cost or constraint |
|---|---|---|
| Flask service extraction | More modular application boundaries | Network contracts and distributed debugging |
| Common database | Continued access to existing application data | Shared schema/write coupling |
| Celery background work | Moves suitable slow work outside request execution | Queue delay, retries, delayed outcomes |
| HTML report templates | Separates content from reusable presentation | Rendering dependencies and pagination complexity |
| Mocked unit tests | Fast isolated behavior checks | Requires integration tests for real wiring |
| Schema-per-tenant, if confirmed | Customer namespace separation | Migration and connection-context complexity |

Operational diagnosis separates request latency, queue waiting time, task duration, and downstream errors. Useful reference signals include task failure rate, oldest waiting-task age, overdue scheduled work, rendering duration, and report memory consumption. Historical EventOps monitoring details are not yet known.

### Actual load-testing regression: eager data loading

I added Django `prefetch_related()` to reduce database calls and expected faster loading. Load testing exposed an approximately 10-second data-loading delay. I also fixed the code by removing prefetch from the initial load and fetching the additional data conditionally in a subsequent call. This kept optional related-data loading off the initial critical path, at the cost of another call when needed.

The exact relation, dominant cost, and after-fix timing are not yet recalled. The observation demonstrates the importance of matching fetch strategy to actual data use, rather than assuming eager loading always improves performance. A detailed incident answer and suggested verification checks are in the [interview document](Interview_Questions_and_Answers.md#actual-load-testing-regression-eager-prefetch-delayed-initial-loading).

### Hosting and deployment on EC2

The application was hosted on Amazon EC2. Docker was used for deployment, with a separate image for each service. Images were built using Docker build commands, then used to run service containers. Nginx routed requests to the backend services.

```text
Service source + Dockerfile
        |
    docker build
        |
Versioned service image
        |
Container deployment on EC2
        |
Nginx routes requests to service
```

This describes the confirmed build/deployment mechanism. Version tagging is a recommended practice in the illustration; the actual tag convention, registry, build location, image transfer, Compose/orchestration tooling, and release automation are unknown. A command such as `docker build -t eventops-spaces:example ./spaces` is an illustrative build, not a historical command or a command executed here. See [Docker build concepts](https://docs.docker.com/build/concepts/overview/); current build internals do not establish the 2019-2021 builder configuration.

Images package code and dependencies; containers run those images. Environment-specific configuration belongs at runtime, and secrets should not be baked into image layers. Updating a container does not itself run safe schema migrations, drain Celery work, or provide zero-downtime rollback. Reference release checks include service readiness, route verification, backward-compatible migrations, and preserving a usable previous image. Exact historical controls remain unverified.

### PDF persistence in Amazon S3

After PDF generation, the generated report was uploaded to an S3 bucket. This separated report storage from the lifecycle of a service container. EC2 supplied application compute; S3 stored report objects; PostgreSQL stored application data. Whether report object keys or status were recorded in PostgreSQL is not yet known.

A reference upload flow is render PDF → upload object → confirm upload success → expose the report as ready. Rendering success and upload success are separate outcomes. A database status update and an S3 upload also do not share a normal database transaction; retry-safe keys and reconciliation are possible controls, not confirmed EventOps mechanisms.

For a reference secure download design, the backend checks user/tenant access before streaming the object or issuing a short-lived presigned URL. Presigned URLs grant time-limited access using the signer's permissions and must be treated as bearer links. Historical URL generation, bucket access settings, credential source, encryption configuration, and retention policy remain unknown. See [S3 presigned URL documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html).

## 14. Implementation notes and sources

Confirmed details and clearly labeled reference explanations are kept separate. Remaining unknowns are the exact deployed service boundaries/names, table/write ownership, inter-service REST details (tentative recollection), tenancy package/context selection, calendar integration, Beat schedule configuration, historical renderer/template engine, SendGrid integration method, EC2 topology/image registry/S3 access configuration, exact auth/decorator configuration and identity propagation, rollout, and exact coverage scope. No private EventOps source code has been inspected.

The 16 GB CSV pipeline, shared LRU cache, piracy analytics, and Oracle/OCI work are not attributed to EventOps without evidence.

Sources:

- Merin's direct clarifications: corrected dates, stack, common database, confirmed Django multi-tenancy with tentative schema isolation, SendGrid, Celery Beat and upcoming-event reminders, SSO/manual login, Nginx mainly for routing, tentative inter-service REST recollection, migration driven by feature complexity/regressions/testing difficulty, Django auth and admin API decorators, SSO-associated calendar access, migration contribution, out-of-office scheduling, Celery PDF tasks and S3 uploads, Django ORM with Q/F expressions, EC2 hosting and per-service Docker images/builds, populated HTML templates, personal WeasyPrint use, pytest/mocking, and 40%-70% coverage.
- [Resume](/Users/merin/workspace/printMyCV/MerinRoseTomSSE7_N.pdf) and [LinkedIn export](/Users/merin/Downloads/LinkedinProfile.pdf): role history, EventOps capabilities, recognition, and career statements.
- Supplied [portfolio](https://merinrose123.github.io/merin-rose-tom/) excerpt: product scope, architecture, frontend, testing, workflows, RBAC, and approximate outcomes. Direct website retrieval was unavailable; the supplied text was used.
- [Official EventOPS website](https://eventops.com/): public product context, accessed 28 October 2026.
- Framework documentation linked within the relevant technical sections supports reference explanations; it does not establish historical versions or implementation.
