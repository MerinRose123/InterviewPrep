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
- [8. Webhooks, polling, SSE, and WebSockets?](#8-webhooks-polling-sse-and-websockets)
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

## 8. Webhooks, polling, SSE, and WebSockets?

| Mechanism | Fit | Cost / failure |
|---|---|---|
| Polling | Simple status observation | Request overhead; backoff and validators |
| Webhook | Server-to-server event notification | Retries, signature verification, replay protection, endpoint failure |
| SSE | Server-to-browser event stream | Reconnect/replay IDs, proxy buffering/timeouts |
| WebSocket | Bidirectional interaction | Stateful connections, auth renewal, backpressure, reconnect |

Webhook receivers should verify signatures over the correct raw payload and check the provider's timestamp/replay scheme, persist durable work, then acknowledge promptly. Deduplicate event IDs. Treat customer-supplied callback URLs as an SSRF boundary, including DNS/redirect/private-network behavior.

**Dig deeper:** reconnects can duplicate or miss events without sequence/replay policy. A socket connection is not durable storage. Which component owns ordering and offline delivery?

## 9. How do you protect and verify an API?

Apply authentication, object/tenant authorization, body-size/time limits, quotas, schema validation, safe errors, and audit trails. Constrain expensive filters/export endpoints separately. Test cross-tenant IDs, duplicate POST, concurrent PATCH, deep pagination, disconnected clients, upstream timeout, and rollout compatibility.

**Interview drill:** design `POST /exports`, status retrieval, cancellation, and download authorization. Explain request identity, storage/queue boundaries, error codes, retry behavior, and cost controls.

## References

- [HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [HTTP caching](https://www.rfc-editor.org/rfc/rfc9111.html)
- [Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html)
- [JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396.html)
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
