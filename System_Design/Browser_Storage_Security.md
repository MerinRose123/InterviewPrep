# Browser Storage and Security Interview Cheat Sheet

[Study index](README.md) · Related: [authentication](Authentication_Authorization.md), [cryptography](Cryptography_Passwords_Secrets.md), [REST](REST_API_Design.md).

Browser examples are explanatory fragments. Storage lifetime and policy can be affected by privacy settings, browser restoration, and user actions.

## Contents

Focused follow-ups: [Login in another tab](#how-is-login-available-in-the-next-tab-without-exposing-a-jwt-to-javascript) · [Multi-tab refresh and logout](#multi-tab-refresh-and-logout-practical-rules).

- [1. Local storage vs. session storage vs. cookies?](#1-local-storage-vs-session-storage-vs-cookies)
- [2. Where should a JWT be stored?](#2-where-should-a-jwt-be-stored)
- [3. What do HttpOnly, Secure, and SameSite actually do?](#3-what-do-httponly-secure-and-samesite-actually-do)
- [4. XSS vs. CSRF vs. CORS?](#4-xss-vs-csrf-vs-cors)
- [5. How should refresh, reload, logout, and multiple tabs work?](#5-how-should-refresh-reload-logout-and-multiple-tabs-work)
- [6. How would you explain your design in an interview?](#6-how-would-you-explain-your-design-in-an-interview)
- [References](#references)

## 1. Local storage vs. session storage vs. cookies?

| Storage | Scope / lifetime | JavaScript access | Automatically sent to server? |
|---|---|---|---|
| `localStorage` | Origin; persists across sessions until cleared/evicted | Yes | No |
| `sessionStorage` | Origin and top-level browsing context; survives reload, normally ends with tab/session | Yes | No |
| Cookie | Host/domain/path rules; session or explicit expiry | Yes unless `HttpOnly` | Yes when cookie/request rules allow |
| In-memory variable | Current JS execution context | Yes | No |
| IndexedDB | Origin; larger structured asynchronous storage | Yes | No |

```javascript
localStorage.setItem("theme", "dark");
sessionStorage.setItem("draft-order", JSON.stringify({productId: 7}));
const draft = JSON.parse(sessionStorage.getItem("draft-order") || "null");
sessionStorage.removeItem("draft-order");
```

Web Storage is synchronous; large operations can block the UI. Session storage is not a secure vault: same-origin injected script can read it. A newly opened page can initially receive a copy from its opener in some situations; subsequent changes are separate. [Web Storage semantics](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API).

**Dig deeper:** origin is scheme/host/port; “site” used by SameSite is a different boundary. What happens with multiple tabs? Never trust a stored role or price just because your UI wrote it.

## 2. Where should a JWT be stored?

A JWT is a format, not a prescribed storage location. First identify the client: browser app, native app, or server. Then choose based on threat model and login/refresh architecture.

| Browser approach | Advantage | Risk / operational cost |
|---|---|---|
| Token in local storage | Easy persistence and bearer-header use | XSS can exfiltrate it; generally avoid storing session credentials here |
| Token in session storage | Tab-limited persistence | Still exposed to XSS; tab scope is not a security defense |
| Access token in memory | Reduces persistent token exposure | Lost on reload; active XSS can still act/read accessible data |
| `HttpOnly` cookie | JS cannot directly read credential | Browser sends it automatically; CSRF defenses required |
| BFF with server-held OAuth tokens | Browser receives a session cookie, not OAuth tokens | Extra backend/session infrastructure; CSRF and XSS still matter |

A reasonable browser architecture to discuss is a same-origin BFF with an opaque, secure session cookie. A pure SPA using bearer tokens has different constraints. Native apps should use platform-protected storage appropriate to the OS.

**Dig deeper:** a cookie can contain an opaque session ID or a JWT. Server-side storage and browser storage are separate decisions. “JWT means stateless” does not eliminate revocation, refresh, or session-risk state.

## 3. What do HttpOnly, Secure, and SameSite actually do?

```http
Set-Cookie: __Host-session=opaque-random-id; Path=/; Secure; HttpOnly; SameSite=Lax
```

`HttpOnly` limits JS reads; `Secure` restricts transport to secure contexts as enforced by browsers; `SameSite` controls cross-site cookie sending. `__Host-` cookies require compatible browser prefix enforcement, Secure, Path=/, and no Domain attribute. Set expiry deliberately and rotate session identifiers at login/privilege changes.

| SameSite setting | Practical behavior / choice |
|---|---|
| `Strict` | Stronger cross-site restriction; can disrupt navigation/login flows |
| `Lax` | Allows selected top-level navigations; not a universal CSRF defense |
| `None; Secure` | Enables cross-site cookie use where browsers permit it; requires deliberate CSRF protection |

[Cookie attribute reference](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).

**Dig deeper:** HttpOnly does not stop XSS from making authenticated requests. Path is not a reliable application security boundary. Third-party cookie restrictions can break cross-site designs.

## 4. XSS vs. CSRF vs. CORS?

| Mechanism | Problem | Defenses / limits |
|---|---|---|
| XSS | Attacker-controlled script executes in your origin | Contextual output encoding, safe DOM APIs, sanitization where necessary, CSP as defense in depth |
| CSRF | Browser sends ambient credentials on an attacker-induced request | Framework CSRF protection, token/origin checks, deliberate SameSite policy |
| CORS | Controls which origins browser JS may read responses from | Explicit allowlist; not authentication and not a general firewall |

Do not disable CSRF merely because the server is called an API or uses JWTs. Check whether credentials are cookies or another automatically attached mechanism. A manually attached bearer header changes the CSRF analysis but does not solve XSS.

```http
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Vary: Origin
```

Do not reflect arbitrary origins. Credentialed browser access cannot use wildcard `Access-Control-Allow-Origin: *`.

**Dig deeper:** some cross-origin requests are sent without preflight; inability to read a response does not mean no server-side effect occurred. Why is a GET endpoint that changes state dangerous?

## 5. How should refresh, reload, logout, and multiple tabs work?

Define access-token lifetime, server session lifetime, refresh rotation, and revocation separately. Coordinate concurrent refreshes so two tabs do not accidentally invalidate one another's token family. A stolen refresh token may outlive a short access token unless rotation/reuse detection and expiry are designed.

Logout should invalidate the server session/refresh capability, clear matching cookies correctly, and clear client state. An already issued access token can remain valid until expiry unless the verifier consults additional revocation state.

**Scenario:** user logs out in tab A but tab B still displays old data. Broadcast a logout notification where appropriate, but enforce access at the server rather than relying on tab coordination. Do not transmit raw credentials in cross-tab messages.

**Dig deeper:** how do you avoid an infinite refresh loop? What if refresh succeeds but the response is lost? Do you require reauthentication for sensitive actions?

### How is login available in the next tab without exposing a JWT to JavaScript?

For a same-origin BFF/session design:

```text
Tab A logs in -> server sets Secure HttpOnly session cookie.
Browser cookie jar holds it for the matching host/path and partition context.
Tab B opens the same app -> GET /session includes the eligible cookie.
Server validates session -> returns safe user/UI data; OAuth tokens stay server-side.
Tab B calls the BFF -> BFF uses/refreshes its server-held API access token.
```

The tabs share access to an eligible cookie through the browser, not by copying it into JavaScript. `HttpOnly` prevents `document.cookie` from reading that credential, but the browser can still attach it to requests. A new tab does not inherit another tab's in-memory access token. In a SPA refresh-cookie design, each tab can bootstrap its own memory-held access token through the protected refresh/session endpoint.

This applies within the same browser profile and applicable cookie scope/partition. A different browser/profile, incognito context or unrelated site does not automatically share the session. Cookies do not use exactly the same boundary as origin storage: they are not isolated by port. Prefer deliberate host scope, HTTPS and separate trusted deployment boundaries. [Cookie rules](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie).

**“Can others take it?”** These controls reduce specific theft paths; they do not make a bearer credential impossible to steal. Another website cannot normally read your origin's storage, but XSS in your app can read localStorage and make authenticated requests even with HttpOnly cookies. A compromised browser, powerful extension or device can exceed web-page protections. Encrypting localStorage with a key accessible to the same application script does not solve active XSS.

### Multi-tab refresh and logout: practical rules

| Event | Browser/app behavior | Server enforcement |
|---|---|---|
| Open another tab | Load `/session` or obtain a tab-local access token through the supported flow | Validate the existing session; do not trust cached UI identity |
| Several requests expire together | Single in-flight refresh in a tab; use supported cross-tab locking if needed | Atomically manage rotation/session state; coordinate BFF replicas |
| Logout in tab A | Clear sensitive UI/draft state as policy requires; notify other tabs | Revoke session/refresh grant and expire the correct cookie |
| Tab B misses logout message | Recheck on resume or next request | Reject revoked session; previously issued JWTs need expiry or additional revocation checks |
| User signs into a different account | Invalidate stale UI caches and bind drafts to the correct account | Recheck ownership; never submit a prior user's draft under a new identity automatically |

`BroadcastChannel` or storage events can carry messages such as `logged-out` or `session-changed`, not raw credentials. They are UI coordination, not authorization. A cross-tab lock alone does not hand a new in-memory access token to every waiting tab; after obtaining the lock, each tab must recheck/bootstrap its own state through the supported architecture. A BFF simplifies this because token refresh happens behind the shared server session.

**Interview answer:** “I can share login across tabs using a host-scoped Secure HttpOnly cookie. JavaScript does not need to read it; the browser attaches it to eligible requests. A BFF keeps OAuth tokens server-side. I still protect against CSRF and XSS and enforce expiry and logout on the server.”

For the complete one-hour form timeline, retry/idempotency rules and refresh failure handling, see [long-form refresh](Authentication_Authorization.md#what-happens-during-a-one-hour-form).

## 6. How would you explain your design in an interview?

“I would first identify client and deployment constraints. For a same-origin browser app, I would evaluate a backend session/BFF and Secure HttpOnly cookie with CSRF protection. If the app must manage OAuth tokens, I would explain token lifetime and XSS exposure, keep refresh handling deliberate, and avoid claiming any storage mechanism eliminates browser compromise.”

This is a design example, not a claim that you implemented it. Use your actual project architecture when describing experience.

**Verify:** test malicious origins, expired sessions, role changes, simultaneous refresh, logout/relogin, cookie scope, and unauthorized record access. Inspect browser network/storage tools without recording live credentials in screenshots or logs.

## References

- [Web Storage API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API)
- [Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie)
- [OWASP HTML5 security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OAuth security best current practice](https://www.rfc-editor.org/rfc/rfc9700.html)
