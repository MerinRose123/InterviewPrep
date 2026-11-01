# Authentication and Authorization Interview Cheat Sheet

[Study index](README.md) · Related: [browser storage](Browser_Storage_Security.md), [cryptography](Cryptography_Passwords_Secrets.md), [Spring security](../Cheatsheets/SpringBoot.md).

Protocol fragments explain flows; use maintained identity-provider/client libraries rather than building production OAuth or JWT validation from scratch.

## Contents

Focused follow-ups: [JWT structure and claims](#jwt-structure-what-is-actually-in-the-token) · [Identifying the user](#how-does-the-backend-identify-the-user) · [JWT algorithms and keys](#which-jwt-algorithms-are-used-and-who-holds-the-key) · [One-hour form and background refresh](#what-happens-during-a-one-hour-form) · [Refresh rotation and races](#rotation-replay-and-simultaneous-refresh).

- [1. Authentication vs. authorization: where are checks enforced?](#1-authentication-vs-authorization-where-are-checks-enforced)
- [2. Session ID vs. JWT: why choose one?](#2-session-id-vs-jwt-why-choose-one)
- [3. OAuth 2.0 vs. OIDC vs. JWT?](#3-oauth-20-vs-oidc-vs-jwt)
- [4. Walk through authorization code with PKCE](#4-walk-through-authorization-code-with-pkce)
- [5. How do refresh, revocation, and key rotation work?](#5-how-do-refresh-revocation-and-key-rotation-work)
- [6. How do services authenticate to each other?](#6-how-do-services-authenticate-to-each-other)
- [7. How would you test and explain this in production?](#7-how-would-you-test-and-explain-this-in-production)
- [References](#references)

## 1. Authentication vs. authorization: where are checks enforced?

Authentication establishes identity; authorization decides whether that identity can perform a specific action on a specific resource. A gateway can authenticate a caller, but the resource-owning service must enforce tenant/owner/action rules.

```python
def read_invoice(principal, invoice_id):
    # Scope the actual query, not just the UI or URL.
    invoice = db.get_invoice(invoice_id, tenant_id=principal.tenant_id)
    require_permission(principal, "invoice:read", invoice)
    return invoice
```

**Failure:** a user changes `/invoices/123` to `/invoices/124` and reads another tenant's invoice. An authenticated token alone does not prevent broken object-level authorization.

| Model | Fit | Tradeoff |
|---|---|---|
| RBAC | Stable roles such as billing-admin | Role explosion; ownership/context still needed |
| ABAC | Tenant, ownership, region, sensitivity, time | Policy complexity and test coverage |
| Relationship-based | Shared documents, organizations, nested groups | Relationship graph consistency and query cost |

**Dig deeper:** deny by default; distinguish platform-admin from tenant-admin. How quickly do role removals take effect when permissions are cached or embedded in tokens?

## 2. Session ID vs. JWT: why choose one?

| Credential | Advantage | Cost |
|---|---|---|
| Opaque session ID | Easy centralized revocation and small browser credential | Session lookup/store availability |
| Signed JWT access token | Services can verify locally | Stale claims, key distribution, revocation strategy |
| Opaque OAuth access token | Central authorization/introspection policy | Introspection latency/cache/failure policy |

A signed JWT commonly has base64url header, payload, and signature. Encoding is readable; signing does not hide claims. JWE encryption is a separate mechanism. Avoid sensitive data in tokens and do not put them in URLs.

```text
Authorization: Bearer <access-token>
# Verifier: allowed algorithm + trusted key + signature + issuer + audience
#           + expiration/not-before + token purpose + authorization policy
```

**Dig deeper:** never trust an arbitrary token-provided key URL. `kid` selects within trusted key material; it is not permission to fetch any URL. Why does merely decoding JWT JSON prove nothing?

### JWT structure: what is actually in the token?

A typical signed JWT uses JWS compact serialization: three dot-separated parts. An encrypted JWE compact token has five parts; “every JWT has three parts” is too broad.

```text
BASE64URL(header JSON bytes).BASE64URL(payload JSON bytes).BASE64URL(signature bytes)

Decoded header (illustrative):
{"alg":"RS256","typ":"JWT","kid":"key-2026-10"}

Decoded payload (illustrative historical timestamps):
{"iss":"https://identity.example.com","sub":"user-42",
 "aud":"invoice-api","iat":1700000000,"exp":1700000900,
 "scope":"invoice:read","tenant_id":"tenant-7","jti":"token-123"}
```

| Field | Meaning / what to check |
|---|---|
| `alg` | Cryptographic algorithm; must match a server-configured allowlist and key type |
| `typ` | Token type hint; enforce the expected token profile/purpose rather than trusting a label alone |
| `kid` | Key identifier within configured trusted keys/JWKS; not a secret or arbitrary URL permission |
| `iss` | Issuer; must match the configured trusted issuer |
| `sub` | Subject; represents the user or other principal under this issuer's token contract |
| `aud` | Intended recipient; the API must be an allowed audience |
| `exp`, `nbf` | Expiry and not-before times; enforce using bounded clock-skew tolerance |
| `iat` | Issued-at time; useful for age policies, not a substitute for expiry |
| `jti` | Token identifier; does not prevent replay without supporting server state/policy |
| `scope`, roles, `tenant_id` | Application/profile claims; validate their semantics and enforce resource permissions |

JWT time claims use seconds since the Unix epoch, not JavaScript milliseconds. Claims above are examples, not a universal set of required JWT fields; the application/token profile defines requirements.

The signing input is the **original encoded header + `.` + original encoded payload**. Editing a claim changes that input and invalidates the signature/MAC. Re-encoding decoded JSON can change byte representation, so use a JOSE library to verify the original token. Anyone possessing a normal signed JWT can decode its claims; signing protects against undetected changes, not reading. [JWT specification](https://www.rfc-editor.org/rfc/rfc7519), [JWS](https://www.rfc-editor.org/rfc/rfc7515).

### How does the backend identify the user?

1. Receive the credential over HTTPS. Treat all decoded fields as untrusted until validation completes.
2. Verify using configured issuer/key trust, allowed algorithm, signature, audience, required claims, time and token purpose.
3. Interpret the validated subject according to the issuer's contract. For federated user identity, map `(iss, sub)` to a local account, for example `(https://identity.example.com, user-42) → local_user_id=731`.
4. Apply account/session policy: disabled account, tenant membership, revocation and permission freshness as required. Local JWT verification alone does not learn that an account was just disabled.
5. Build a request principal and enforce action, owner and tenant checks at the resource. A validated identity does not authorize every record.

OIDC defines the issuer/subject pair as the stable identity mapping; email can change and should not be used for automatic cross-provider account linking. An access-token subject can represent a service instead of a human. The token normally establishes possession of a bearer credential: a thief holding it can impersonate the principal until blocked/expired. It does not prove the original human is still present. [OIDC subject semantics](https://openid.net/specs/openid-connect-core-1_0.html#ClaimStability).

**Interview answer:** “The issuer puts a subject identifier in the token. My API verifies the token before trusting that subject, maps the trusted issuer and subject to the application identity, and then checks permission for the requested resource.”

### Which JWT algorithms are used, and who holds the key?

| JOSE algorithm | Mechanism | Key ownership / consequence |
|---|---|---|
| `HS256` | HMAC with SHA-256 | Issuer and verifiers share a high-entropy secret; every verifier can also mint tokens |
| `RS256` | RSA PKCS#1 v1.5 signature with SHA-256 | Issuer holds private key; services use public key to verify |
| `PS256` | RSA-PSS signature with SHA-256 | Private signing/public verification; requires compatible provider/library support |
| `ES256` | ECDSA using P-256 and SHA-256 | Private signing/public verification; compact signatures, vetted implementation essential |

These are integrity/authenticity mechanisms, not encryption. HS256 uses a MAC rather than an asymmetric digital signature. Do not put a signing secret/private key in a browser app. Public verification keys can be distributed through a trusted issuer's JWKS. Configure accepted algorithms independently; reject unsigned `alg=none` tokens in this signed-token design and prevent symmetric/asymmetric key confusion. [Algorithm definitions](https://www.rfc-editor.org/rfc/rfc7518), [JWT security BCP](https://www.rfc-editor.org/rfc/rfc8725.html).

**Follow-up:** changing RS256 to HS256 in a token must never make the API treat an RSA public key as an HMAC secret. Decoding a token on the frontend can guide UI behavior but cannot replace server authorization.

## 3. OAuth 2.0 vs. OIDC vs. JWT?

| Term | What it supplies | Practical use |
|---|---|---|
| OAuth 2.0 | Delegated authorization framework | Let a client call an API with authorized scope |
| OIDC | Identity layer on OAuth; ID token and identity semantics | User sign-in / identity federation |
| JWT | Token representation | Can represent ID tokens or access tokens, but not all access tokens are JWTs |

OIDC ID tokens are intended for the client to understand the authenticated session. API authorization generally uses an access token intended for that API. Validate ID token issuer, signature, audience, time, and nonce when applicable. Do not substitute an ID token for an API access token. [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html).

**Dig deeper:** what do scope and audience each constrain? “Login with provider” needs identity semantics, not simply any OAuth token you received.

### A concrete OAuth vs. OIDC example

- **OAuth:** a calendar application receives permission to read your calendar. The access token is for the calendar API; scope specifies the permitted operation. OAuth also supports machine-to-machine access, with no human user sign-in.
- **OIDC:** “Sign in with an identity provider” requests `openid` and supplies an ID token that the client validates to establish the user's identity. Optional profile claims/UserInfo provide additional identity data.
- **JWT:** a representation that may carry those claims. OIDC ID tokens are JWTs; OAuth access tokens may be JWTs or opaque strings. Refresh tokens are not required to be JWTs.

| Credential | Consumer | Purpose |
|---|---|---|
| Authorization code | Token endpoint | Short-lived, single-use input exchanged with the flow's required protections |
| ID token | Login client / relying party | Evidence of authentication to that client |
| Access token | Intended resource API | API access within audience/scope and server policy |
| Refresh token | Authorization server's token endpoint | Obtain new access tokens under the continuing grant |

**Scope vs. audience:** `invoice:read` describes delegated permission; `invoice-api` identifies the intended recipient. A token for a different API is not acceptable merely because it contains a familiar scope. A refresh token is not sent to the invoice API. [OAuth framework](https://www.rfc-editor.org/rfc/rfc6749), [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html).

## 4. Walk through authorization code with PKCE

```text
1. Client creates a random verifier and stores it for this login attempt.
2. challenge = BASE64URL(SHA256(ASCII(verifier))) without '=' padding.
3. Browser -> authorization endpoint:
   response_type=code, client_id, redirect_uri, scope=openid,
   code_challenge, code_challenge_method=S256, state, nonce
4. Provider authenticates/consents and redirects with code + state.
5. Client validates response binding and exchanges code + verifier at token endpoint.
6. Provider checks verifier/challenge binding; client validates resulting tokens.
```

```python
import base64
import hashlib
import secrets
verifier = secrets.token_urlsafe(32)
challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode("ascii")).digest()
).rstrip(b"=").decode("ascii")
```

PKCE binds authorization-code redemption to the client instance that initiated the flow; an intercepted code alone is insufficient. It is not encryption or user authentication. Public clients cannot keep a static client secret confidential. Confidential clients can use client authentication as well as PKCE. [PKCE specification](https://www.rfc-editor.org/rfc/rfc7636).

**Dig deeper:** `state`, OIDC `nonce`, and PKCE have different response/session binding purposes; use a maintained library's correctly configured flow. Require exact approved redirect matching and HTTPS except documented native/local development exceptions. Avoid implicit/password flows; see [OAuth security guidance](https://www.rfc-editor.org/rfc/rfc9700.html).

## 5. How do refresh, revocation, and key rotation work?

Short-lived access tokens limit exposure but do not provide immediate revocation. Refresh tokens are high-value credentials; keep them out of ordinary API calls, rotate/bind them appropriately, and define replay/reuse handling. Server-side session revocation and already issued access-token validity are separate.

| Change | Strategy | Failure to consider |
|---|---|---|
| User logout | Revoke session/refresh capability | Previously issued access token can still verify |
| Role removal | Short validity, introspection, or policy/version lookup | Cached claims remain stale |
| Signing-key rotation | Publish new public key, transition signing, retain old verification keys for overlap | Premature removal invalidates legitimate tokens |
| Key compromise | Revoke affected trust, rotate, constrain token validity | Normal overlap may be inappropriate during compromise |

**Dig deeper:** JWKS caching needs bounded refresh and outage behavior. A never-before-seen `kid` should not cause unlimited upstream fetches. What is the clock-skew allowance and why isn't it unlimited?

### What happens during a one-hour form?

Example lifetimes below are illustrative: access token 15 minutes, refresh grant/session longer with both idle and absolute limits. The JWT does **not** renew itself; an application, SDK or BFF makes a separate refresh request.

```text
00:00  Login -> access token A1; refresh capability established.
00:15  A1 expires while the user is typing. The form can remain open.
00:40  Autosave or another API call needs authentication.
       App/BFF obtains A2 using a valid refresh grant, then sends the call.
01:00  Submit -> ensure usable authentication, then submit the preserved draft.
```

Two possible designs:

- **BFF:** browser sends its session cookie to the BFF. The BFF loads server-held OAuth tokens and refreshes when needed before calling the API. The browser does not handle the OAuth refresh token.
- **SPA with an application refresh endpoint:** access token stays in memory; a refresh credential can be in a Secure HttpOnly cookie managed by that endpoint. The browser sends the cookie under applicable request rules; the endpoint validates session/CSRF protections and returns a fresh access token. A direct OAuth public client must follow its provider's supported token flow; it cannot assume the provider sets an app-domain cookie.

Refresh can be proactive shortly before expiry, or on demand before a request. An expired-token response can trigger one coordinated refresh and at most one appropriate retry. Do not refresh on every `401`, on authorization `403` errors, or recursively on refresh failure. A decoded client-side `exp` helps scheduling but is not a security decision.

Timers can be throttled in background tabs; devices sleep and networks fail. Recheck on resume and before requests. A form that performs no network calls may need no refresh until submission. Typing alone does not necessarily extend server idle expiry; background refresh should not silently defeat the intended idle policy.

Preserve the draft through token expiry and reauthentication. Choose server autosave or browser draft storage based on data sensitivity; do not store credentials with the draft. Retry writes only when known safe: a transport timeout may occur after the server committed the operation, so use idempotency keys/deduplication for submissions. If refresh is expired/revoked or requires interaction, request sign-in and resume the draft without bypassing authorization.

**Interview answer:** “The form and access-token lifetime are separate. Before autosave or submit, the app or BFF gets a fresh access token using the valid refresh grant. I coordinate refreshes, preserve the draft, and ask for login if refresh fails. I don't keep an expired JWT valid or depend only on a timer.”

### Rotation, replay and simultaneous refresh

With rotation, the authorization server replaces refresh token R1 with R2 and invalidates R1. Later reuse of R1 can indicate theft and trigger revocation of the active token family. For public clients, OAuth security BCP requires refresh tokens to be sender-constrained or use rotation to detect replay. This does not mean every deployment must use the identical mechanism. [Refresh-token protection](https://www.rfc-editor.org/rfc/rfc9700.html#section-4.14).

Use one in-flight refresh per session where practical. A BFF can coordinate in its server session store across replicas; a process-local promise only coordinates one process. Browser tabs need additional coordination if they share rotating refresh credentials. Browser locks can help where supported, but server/provider correctness must handle races too.

A response lost after successful rotation is ambiguous: blindly retrying R1 may look like reuse. Use the provider's documented recovery/concurrency policy; any overlap allowance needs a bounded security tradeoff. Never disable reuse protection globally to hide refresh races. Define expiry, revocation and forced-login behavior explicitly.

## 6. How do services authenticate to each other?

Use workload identity, mutually authenticated TLS, or a provider-supported client-credentials/token exchange mechanism. Separate end-user identity from the service's identity and delegation authority. Do not blindly propagate a token to a service outside its audience.

**Scenario:** export worker runs hours after the user submits a job. Persist tenant/operation ownership and re-evaluate the policy appropriate for the job; do not depend on a browser's short-lived token remaining valid forever.

**Dig deeper:** mTLS identifies a workload connection but does not automatically authorize every tenant action. How are credentials issued/rotated? What prevents a confused-deputy service from using its broad privileges on an attacker's request?

## 7. How would you test and explain this in production?

Test expired tokens, wrong audience/issuer, disallowed algorithms, cross-tenant IDs, role changes, refresh races, signing-key rollover, and provider outages. Log decision reason codes and correlation IDs, not credentials. Rate-limit credential endpoints and use generic login/reset responses where appropriate to reduce account enumeration.

**Interview drill:** trace browser sign-in → callback → session/token → API → service permission check → DB tenant filter. At every hop explain the trusted issuer, intended audience, and failure behavior.

## References

- [OAuth security BCP](https://www.rfc-editor.org/rfc/rfc9700.html)
- [PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html)
- [JWT best current practices](https://www.rfc-editor.org/rfc/rfc8725.html)
- [OWASP authorization](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
