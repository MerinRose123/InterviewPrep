# REST and API Design Interview Cheat Sheet

[Study index](README.md) · Related: [authentication](Authentication_Authorization_CheatSheet.md), [browser security](Browser_Storage_Security_CheatSheet.md), [microservices](Microservices_CheatSheet.md).

HTTP syntax is illustrative. Distinguish standardized HTTP behavior from application conventions such as an idempotency-key contract.

## Contents

- [1. What makes an API RESTful, and how do you model resources?](#1-what-makes-an-api-restful-and-how-do-you-model-resources)
- [2. GET vs. POST vs. PUT vs. PATCH vs. DELETE?](#2-get-vs-post-vs-put-vs-patch-vs-delete)
- [3. Which status code should you return?](#3-which-status-code-should-you-return)
- [4. How do you implement idempotency and concurrent updates?](#4-how-do-you-implement-idempotency-and-concurrent-updates)
  - [Interview example: create an order safely on retry](#interview-example-create-an-order-safely-on-retry)
- [5. Offset vs. cursor pagination?](#5-offset-vs-cursor-pagination)
- [6. How do caching, versioning, and compatibility work?](#6-how-do-caching-versioning-and-compatibility-work)
- [7. How do you design an asynchronous API?](#7-how-do-you-design-an-asynchronous-api)
- [8. REST vs WebSocket vs SSE vs Webhook vs Polling — senior interview deep dive](#8-rest-vs-websocket-vs-sse-vs-webhook-vs-polling--senior-interview-deep-dive)
- [9. How do you protect and verify an API?](#9-how-do-you-protect-and-verify-an-api)
- [References](#references)

## 1. What makes an API RESTful, and how do you model resources?

REST uses constraints including client/server separation, stateless requests, cacheability, a uniform interface, and layers. Many practical JSON APIs use a subset; explain the actual contract rather than treating endpoint naming as the definition.

```http
POST /v1/exports
Content-Type: application/json
Authorization: Bearer <token>

{"datasetId":"d42","format":"pdf"}
```

Model long-running work as a resource, not an indefinitely blocked request. For commands with clear domain semantics, a documented operation resource can be clearer than forcing every action into generic CRUD.

**Dig deeper:** stateless requests do not prohibit a database or authentication session store; each request must carry the information needed for its processing under the API design. How do retries identify the same operation?

## 2. GET vs. POST vs. PUT vs. PATCH vs. DELETE?

| Method | Intended semantics | Practical trap |
|---|---|---|
| GET / HEAD | Safe retrieval / response metadata | Do not make business mutations on GET |
| POST | Resource-specific processing, often creation | Not inherently idempotent; define retry behavior |
| PUT | Create/replace target representation | Distinguish replacement from partial update |
| PATCH | Partial modification with defined patch semantics | Idempotence depends on patch operation |
| DELETE | Remove target association/resource per contract | Repeated status codes may differ while intended effect remains idempotent |

Idempotence means repeating the request has the same intended effect, not identical responses or no logging. `PATCH add 1` differs from `PATCH set quantity=5`. [HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html).

**Dig deeper:** if POST times out after creation, a retry can duplicate work. A client-generated resource ID + PUT or an explicit idempotency contract can help where appropriate.

## 3. Which status code should you return?

| Code | Use / scenario |
|---|---|
| 200 / 201 / 204 | Success / creation with Location / success without body |
| 202 | Accepted but not finished; provide a status resource |
| 400 / 422 | Malformed/request validation vs. semantically unprocessable content under your documented contract |
| 401 / 403 | Missing/invalid authentication vs. authenticated-but-denied, with deliberate resource-hiding policy |
| 404 | Missing or intentionally concealed resource |
| 409 | Conflict with current resource state |
| 412 | Conditional request precondition failed |
| 429 | Rate limit; provide useful retry guidance |
| 502 / 503 / 504 | Upstream gateway failure / unavailable service / gateway timeout |

Do not return HTTP 200 for every error. Keep machine-readable error categories stable and avoid exposing stack traces or secrets.

```http
HTTP/1.1 409 Conflict
Content-Type: application/problem+json

{"type":"https://api.example.com/problems/order-state",
 "title":"Order state conflict","status":409,
 "detail":"A shipped order cannot be cancelled.","instance":"/requests/r42"}
```

[Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) supplies a standard error representation; your domain extension fields still need a contract.

## 4. How do you implement idempotency and concurrent updates?

```http
POST /v1/payments
Idempotency-Key: tenant7-checkout-42
Content-Type: application/json

{"orderId":"42","amountMinor":2500,"currency":"INR"}
```

Scope the key to identity/operation; persist request fingerprint and result; enforce uniqueness atomically. Same key + different body should conflict. Define in-progress responses, retention duration, and replay after expiry. A local memory dictionary does not cover restarts/replicas.

```http
PATCH /v1/orders/42
If-Match: "version-7"
Content-Type: application/merge-patch+json

{"deliveryNote":"Reception"}
```

Evaluate the precondition and update atomically in storage. ETag-based conditional writes can prevent lost updates; the ETag must represent the state you protect. A token merely checked in controller code before a separate unguarded write is race-prone.

**Dig deeper:** should two concurrent identical requests wait or return “in progress”? What if the external charge succeeded but saving the response failed?

### Interview example: create an order safely on retry

**Question:** “Order API: input is `user_id` and product details. If the request fails and is retried, it should not create another order. Write pseudocode.”

**Answer:** the client generates one idempotency key for each intended order and reuses it on retries. Persist the key, order, and response in one database transaction, with a unique constraint on `(user_id, operation, key)`.

```text
// Client: create the key once, outside the retry loop.
key = randomUUID()
retryOnTransientFailure:
    POST /v1/orders
    Idempotency-Key: key
    Body: { user_id, product_details }

// Server: authenticatedUser supplies the trusted identity.
function createOrder(authenticatedUser, key, request):
    validateKeyAndRequest(key, request)
    require request.user_id == authenticatedUser.id
    scope = (authenticatedUser.id, "create_order", key)
    fingerprint = hash(canonicalize(request))

    BEGIN TRANSACTION  // READ COMMITTED
    try:
        claimed = INSERT idempotency_record(scope, fingerprint)
                  ON UNIQUE CONFLICT DO NOTHING
                  RETURN whether_inserted
        // Atomic insert, not a separate existence check.
        // A competing insert waits for the first transaction to finish.
        // If it rolls back, this insert can succeed instead.

        if not claimed:
            previous = SELECT idempotency_record WHERE scope = scope
            // Fresh statement sees the competing transaction's commit.
            ROLLBACK
            if previous.fingerprint != fingerprint:
                return 409, "Key already used for a different request"
            return previous.saved_status, previous.saved_response

        order = INSERT order(authenticatedUser.id, request.product_details)
        response = { order_id: order.id, status: "created" }
        UPDATE idempotency_record WHERE scope = scope
            SET saved_status = 201, saved_response = response
        COMMIT
        return 201, response
    catch database_error:
        ROLLBACK if transaction is still active
        return retryable_error  // Client retries with the SAME key.
```

The insert syntax is pseudocode for database-supported conflict handling, such as PostgreSQL `ON CONFLICT DO NOTHING`; it must not abort the transaction on a duplicate. The replay read uses the primary database. This example assumes records remain available throughout the retry window, with no concurrent expiry deletion.

| Failure / retry | Result |
|---|---|
| Order commits, but the response is lost | Retry returns the saved response and the same order ID |
| Failure before commit | Both order and key reservation roll back; retry can create the order |
| Commit outcome is unknown after a connection failure | Retry with the same key resolves whether the order committed |
| Two requests arrive with the same key | Unique constraint serializes the claim; only one order is created |
| Same key, different product details | Return a conflict rather than silently replaying a different order |

**What to say aloud:** “The key identifies the intended operation. The unique constraint handles concurrent retries, and the transaction keeps order creation and the saved result atomic.”

Do not derive the key only from `user_id + product_details`: a user may intentionally buy the same products twice. Each new intended order needs a new key. After key expiry, this deduplication guarantee no longer applies; document the supported retry window.

**Scope:** this transaction covers local database writes. External payment calls or messages need their own idempotency/recovery design, such as a provider idempotency key and a transactional outbox. A database rollback cannot undo an external charge.

## 5. Offset vs. cursor pagination?

| Approach | Fit | Tradeoff |
|---|---|---|
| Offset/limit | Small data, random page navigation | Deep offsets cost work; inserts/deletes shift pages |
| Keyset/cursor | Large ordered feeds | Needs stable sort/tie-breaker; arbitrary page jumps harder |
| Snapshot export | Consistent complete data view | Snapshot lifetime/storage/transaction cost |

```sql
SELECT id, created_at FROM orders
WHERE tenant_id = :tenant
  AND (created_at, id) < (:cursor_time, :cursor_id)
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

Cursor should bind sorting/filter scope and tenant as needed; encode/sign it according to tampering/privacy requirements. Base64 alone is not integrity protection. Keyset pagination does not by itself freeze a changing dataset.

**Dig deeper:** validate maximum page size and allowed sort/filter fields. Which composite index supports this query? What happens when a row's sort key changes?

## 6. How do caching, versioning, and compatibility work?

Use cache validators/freshness for safe data, versioned asset URLs for immutable content, and private/no-store policies for sensitive responses as appropriate. See [caching](Caching_Performance_CheatSheet.md) for headers and shared-cache hazards.

Prefer additive compatible schema changes where possible, but even an added enum value can break strict clients. Document deprecation, provide migration windows, and use consumer contract tests. URL versioning is explicit; header/media-type versioning can complicate routing and discovery.

**Dig deeper:** does an old client ignore unknown fields? How do you distinguish absent from explicit null in a PATCH? Are timestamps timezone-qualified and money units explicit?

## 7. How do you design an asynchronous API?

```http
HTTP/1.1 202 Accepted
Location: /v1/exports/e42
Retry-After: 3

{"id":"e42","status":"QUEUED"}
```

Persist operation before acknowledging acceptance, usually with an outbox/queue intent. A status resource exposes queued/running/succeeded/failed/cancel-pending states, progress semantics, and authorized download metadata. A percentage must describe a meaningful denominator, not fabricated progress.

**Dig deeper:** does cancel mean guaranteed stop or a best-effort request? How do you report a partially completed export? What is status retention and download expiry?

## 8. REST vs WebSocket vs SSE vs Webhook vs Polling — senior interview deep dive

**30-second answer:** REST is an architectural style built around stateless HTTP requests and resource representations. WebSocket is a persistent, bidirectional messaging protocol. Server-Sent Events (SSE) stream one-way updates from server to client over an HTTP response. A webhook is an event-triggered HTTP callback, usually between servers. Polling periodically asks for updates; long polling waits until an event or timeout and then repeats. They can coexist in one application.

### Comparison table: direction, state, connection, delivery

| Question | REST over HTTP | WebSocket | SSE | Webhook | Polling / long polling |
|---|---|---|---|---|---|
| Who initiates? | Client | Client establishes handshake; either side sends after | Client subscribes; server streams | Event producer calls registered receiver | Client |
| Data direction | Request and response | Full duplex, both ways | Server → client on stream; separate HTTP requests for client commands | Producer → receiver; receiver sends HTTP response | Client request → server response |
| Stateless? | **REST constraint: stateless requests**; server can still use DB/shared session store | **Connection-stateful**: server tracks active socket; app messages may be self-contained | **Long-lived stream state**; underlying HTTP semantics remain stateless | **Individual HTTP deliveries stateless**; processing can be stateful | HTTP requests stateless; outstanding long-poll request occupies connection/stream |
| Connection | HTTP request/response; transport connection can be reused | Long-lived WebSocket connection | Long-lived HTTP response | Usually independent HTTP requests, connection may be reused | Repeated requests; long poll holds a request open |
| Protocol / format | HTTP methods, resource representations | WebSocket frames, ws/wss | HTTP, \`text/event-stream\`, UTF-8 | Usually HTTP POST with JSON payload | HTTP |
| Automatic browser reconnect | Application/client logic | Must implement | Native \`EventSource\` normally reconnects | Sender-specific retry policy | Client logic |
| Built-in durable delivery? | No; application designs retries and storage | No | No; IDs can support replay **if server retains events** | No; delivery/retries depend on provider | No |
| Typical scale bottleneck | Request rate, DB, downstream latency | Concurrent sockets, fan-out, buffers | Open streams, proxy buffering, fan-out | Delivery queue, retries, receiver availability | Poll frequency, held requests |
| Good fit | CRUD, commands, status reads | Chat, multiplayer, collaborative editing | Job progress, notification feed, token streaming | Payment status, GitHub events, third-party integrations | Simple status checks, legacy clients |

**Critical nuance:** "Stateless" and "persistent connection" describe different layers. HTTP is stateless even when TCP/TLS connections are reused. SSE holds one HTTP response open but does not make REST-style requests inherently stateful. WebSocket servers must track connection lifecycle, but business state can still live in shared storage. A webhook is a delivery pattern, not a separate transport protocol.

### Interviewer follow-ups with strong answers

**Q1. Is REST stateless? Can a REST service use Redis sessions or a database?**

REST's stateless constraint means each request carries enough context to interpret and process it; the server should not depend on hidden conversational context from earlier requests. Persisted resource state is normal. Authentication via bearer tokens or a session lookup can work, but relying on a particular in-memory server instance for the next request makes scaling and failover fragile. HTTP keep-alive does not change REST statelessness.

**Q2. Are WebSockets stateful? Can you scale them horizontally?**

The **connection** is stateful: a backend instance holds an open socket and its subscriptions. For multiple instances, publish events through a shared fan-out layer (e.g., Redis Pub/Sub or a broker), route to the instances holding subscribed clients, and use shared durable storage for history. Handle reconnects, reauthentication, heartbeats, slow consumers, and connection limits. Sticky sessions can simplify routing but are not a substitute for cross-instance delivery or durability.

**Q3. Is SSE stateful or stateless?**

The HTTP protocol is stateless, but the server maintains an active streaming response and related connection resources. An SSE stream can be reconstructed from an authenticated request plus a cursor/event ID. Browser \`EventSource\` automatically reconnects in normal circumstances, but resuming missed events requires server-side history and handling of \`Last-Event-ID\`; reconnection alone does not guarantee lossless delivery.

**Q4. Is a webhook stateless? Does it guarantee exactly-once delivery?**

Each webhook is an ordinary HTTP request, so the receiver can be stateless at the request-processing layer while persisting event IDs and business updates. Many providers retry; duplicate or out-of-order deliveries are possible. Verify signatures and timestamps, deduplicate using a stable event ID, enqueue expensive processing, and return a timely 2xx after durable acceptance. Never assume exactly-once execution.

**Q5. SSE vs WebSocket: which for live notifications?**

Prefer SSE when the browser only needs server-to-client updates: simpler HTTP semantics, event IDs, and browser reconnection. Prefer WebSocket when both sides exchange frequent low-latency messages, such as chat, cursor movements, or interactive collaboration. For SSE, check reverse-proxy buffering, idle timeouts, heartbeat comments, per-origin connection limits under HTTP/1.1, and HTTP/2 stream limits.

**Q6. SSE vs long polling?**

SSE streams **multiple** events on one response. Long polling holds a request until a change or timeout, sends a response, and then the client starts another request. Ordinary polling checks at fixed intervals even when nothing changes. Polling is easiest to debug but wastes requests or introduces latency; SSE needs careful connection management.

**Q7. Why not use WebSockets for everything?**

They add persistent connection management, authentication renewal, heartbeat handling, backpressure, fan-out, and reconnection. REST is simpler for ordinary commands and cacheable resource reads. A system can use REST to create a job and SSE to stream its progress; using WebSocket for a one-way progress feed may be unnecessary complexity.

**Q8. What happens if the SSE/WebSocket client disconnects?**

The job should continue independently of the network connection if its business semantics require that. Store job state and results durably; the client reconnects and retrieves current state via REST, then resumes live events. Event streams are notification channels, **not** authoritative job-state stores.

**Q9. How do you authenticate and authorize these mechanisms?**

REST: normal authentication and per-resource authorization. WebSocket: authenticate the handshake and enforce authorization on every subscription/action; account for credential expiry on long-lived sockets. SSE: authenticate the stream request and filter events by authorized user/tenant; browser \`EventSource\` does not offer arbitrary custom request headers, so cookie-based authentication or an appropriate client approach may be needed. Webhook: verify the sender's signature against the **raw request body**, reject replayed timestamps/IDs, and protect callback destinations against SSRF when sending.

**Q10. Does a WebSocket message use HTTP?**

The classic WebSocket opening handshake uses HTTP/1.1 Upgrade, after which application messages use WebSocket frames rather than ordinary HTTP request/response messages. WebSockets can also be established over newer HTTP versions using their specified mechanisms. SSE stays an HTTP response stream.

**Q11. Can REST be real time?**

REST endpoints can be polled, including long polling, but REST itself does not provide server push. You can combine REST commands and resource reads with SSE or WebSocket updates.

**Q12. What is the difference between an event broker and these client communication methods?**

Kafka, RabbitMQ, and Redis messaging are backend messaging technologies. SSE and WebSocket deliver events to connected clients; webhooks deliver HTTP notifications to external services. A backend broker can distribute updates across application instances, but using SSE/WebSocket does **not** imply Kafka is part of the architecture.

### Practical design exercise: background PDF export

1. Client sends \`POST /reports\` over REST; server returns \`202 Accepted\` with \`job_id\`.
2. Worker executes the job; job status is persisted independently of browser connectivity.
3. Browser opens \`GET /reports/{job_id}/events\` using SSE for progress (or polls \`GET /reports/{job_id}\`).
4. If the browser disconnects, it reads current status via REST on reconnect; replay is optional if the server stores event IDs/history.
5. When complete, the client fetches an authorized download URL. If an external partner must be notified, send a signed webhook with retries and event-ID deduplication.
6. Choose WebSocket instead of SSE **only if** frequent two-way interactive controls are needed.

**Whiteboard follow-up:** 10,000 connected browsers across four backend instances: explain load-balancer timeouts, which instance holds each socket/stream, fan-out, heartbeat frequency, buffer limits, reconnect storms, and why a durable job store is independent of the push channel.

### Minimal wire examples

\`\`\`http
GET /reports/42/events HTTP/1.1
Accept: text/event-stream

HTTP/1.1 200 OK
Content-Type: text/event-stream

id: 101
event: progress
data: {"job_id":"42","percent":60}

\`\`\`

\`\`\`http
POST /webhooks/report-complete HTTP/1.1
Content-Type: application/json
X-Event-ID: evt_123
X-Signature: <provider-specific-signature>

{"job_id":"42","status":"completed"}
\`\`\`

**Interview traps:** WebSocket is not automatically durable; SSE is not bidirectional; REST is not the same as "new TCP connection for every request"; a webhook does not guarantee delivery once; long polling is not SSE; "stateful connection" does not imply stateful business storage.


## 9. How do you protect and verify an API?

Apply authentication, object/tenant authorization, body-size/time limits, quotas, schema validation, safe errors, and audit trails. Constrain expensive filters/export endpoints separately. Test cross-tenant IDs, duplicate POST, concurrent PATCH, deep pagination, disconnected clients, upstream timeout, and rollout compatibility.

**Interview drill:** design `POST /exports`, status retrieval, cancellation, and download authorization. Explain request identity, storage/queue boundaries, error codes, retry behavior, and cost controls.

## References

- [HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [HTTP/1.1 persistent connections](https://www.rfc-editor.org/rfc/rfc9112.html)
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [MDN: WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [HTTP caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- [Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html)
- [JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html)
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
