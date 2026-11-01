# Frontend Interview Questions: Concepts and Code

Start with the short answer, explain one example, then discuss a tradeoff or failure case. Examples are study snippets; JSX requires a React setup. React examples use function components. Angular examples and terminology refer to Angular, not AngularJS; check the version used by your project.

Study in order, or jump directly to the framework you need. Keep each answer to 30–60 seconds before going deeper.

- [Fundamentals](#fundamentals): [DOM](#what-is-the-dom-what-data-structure-is-behind-it), [framework choices](#why-react-or-angular-instead-of-plain-htmlcss), [components](#what-is-a-component), [side effects](#what-is-a-side-effect), [Promises](#what-is-a-promise), [async/await](#asyncawait-and-error-handling), [event loop](#event-loop-and-output-questions), [JavaScript](#javascript-fundamentals), [HTML/CSS/accessibility](#html-css-and-accessibility), [browser storage/security](#browser-storage-and-security), [scenarios](#practical-frontend-scenarios).
- [Angular](#angular): [TypeScript](#typescript-what-does-it-add-to-javascript), [component communication](#how-do-components-communicate), [lifecycle](#constructor-vs-ngoninit-vs-ngonchanges), [forms](#reactive-forms-vs-template-driven-forms), [RxJS](#promise-vs-observable-and-which-rxjs-operator-should-i-choose), [routing](#guards-resolvers-and-lazy-routes), [change detection](#change-detection-onpush-and-signals).
- [React](#react): [component example](#react-component-example), [props/state/rendering](#props-state-rendering-and-keys), [Hooks](#what-are-react-hooks), [side effects](#side-effects-in-react), [useEffect](#how-does-useeffect-work).

## Fundamentals

Browser and JavaScript concepts apply to both Angular and React. Start here before the framework sections.

### What is the DOM? What data structure is behind it?

**Interview answer:** The Document Object Model is the browser's object representation and programming interface for a document. JavaScript can use it to read and change content, structure, and events. Its core structure is a rooted, ordered tree of nodes.

```html
<html>
  <body>
    <div><p>Hello</p><button>Save</button></div>
  </body>
</html>
```

```text
Document
└── html
    ├── head (the HTML parser can insert this)
    └── body
        └── div
            ├── p
            │   └── Text: Hello
            └── button
                └── Text: Save
```

Whitespace can create additional text nodes; this diagram omits them. Nodes include documents, elements, text, and comments. An element can have many children, so this is **not a binary tree**. Parent/child and sibling relationships let APIs traverse it. Attributes belong to elements; they are not ordinary children in the document tree.

**HTML vs. DOM:** HTML is markup/source. The browser parses it into the live DOM, possibly correcting invalid markup. JavaScript can change the DOM without changing the original HTML response.

```javascript
const message = document.querySelector("p");
if (message) message.textContent = "Saved";
```

**Follow-up: complexity?** Walking all nodes with DFS/BFS is O(n); DFS uses O(height) stack space and BFS O(maximum width) queue space. Do not claim every DOM lookup is O(n): browsers can maintain indexes and optimize selectors. The DOM API does not prescribe a universal internal memory layout or lookup complexity.

**DOM vs. render tree vs. virtual DOM:** The DOM models the document. Style calculation and layout determine what is displayed and where; the rendering structures are separate. React maintains in-memory UI descriptions and reconciles updates before committing DOM changes. A virtual DOM is not a copy of every browser DOM feature and does not guarantee better performance than carefully written DOM code. Angular should not be described as using React's virtual DOM model.

### Why React or Angular instead of plain HTML/CSS?

**Interview answer:** HTML defines structure and semantics; CSS controls presentation. JavaScript handles application behavior and dynamic updates. React and Angular help organize interactive applications into components and keep displayed UI consistent with application state. They still use browser HTML, CSS, JavaScript, and DOM facilities.

The fair comparison for a dynamic application is **plain HTML/CSS/JavaScript versus a UI library/framework**, not HTML/CSS alone.

Example: an event-booking screen has filters, selected slots, availability checks, validation, loading states, and errors. With manual DOM code, developers must coordinate each update. Components and state-driven rendering make that coordination easier as the screen grows.

| Approach | Fits well | Cost / tradeoff |
|---|---|---|
| Plain HTML/CSS with small amounts of JS | Static content, simple forms, a few interactions | Manual state coordination can become difficult as behavior grows |
| React | Component-based interactive UI with flexible ecosystem choices | Routing/data tools and conventions need deliberate selection; build/runtime costs |
| Angular | Applications benefiting from integrated conventions, DI, routing, and forms | More framework concepts and upgrade considerations |

Do not say frameworks are mandatory, automatically faster, or make websites secure. A server-rendered page with progressive enhancement can handle many real products well. Choose based on interaction complexity, team experience, accessibility, delivery constraints, and maintenance.

### What is a component?

**Interview answer:** A component is a unit of UI with a defined responsibility. It combines presentation and behavior, receives inputs, and may manage local state. Components compose into larger screens.

**Good boundary:** one coherent responsibility, a clear interface, and independently understandable behavior. Do not split every HTML element into a component just to increase reuse.

### What is a side effect?

**Interview answer:** A side effect is an interaction beyond returning a calculated value, such as modifying external state, sending a request, writing storage, or installing a subscription. A pure function returns the same result for the same inputs and does not change external state.

```javascript
// Pure calculation:
const total = prices => prices.reduce((sum, price) => sum + price, 0);

// Side effects:
localStorage.setItem("theme", "dark");
console.log("Saved");
```

### What is a Promise?

**Interview answer:** A Promise represents an eventual asynchronous result. It is pending, then becomes fulfilled with a value or rejected with a reason. Once settled, its outcome cannot change.

- `.then()` transforms a successful result and returns a new Promise.
- `.catch()` handles rejection and can recover by returning a value, or propagate failure by throwing.
- `.finally()` performs cleanup regardless of outcome. Normally it preserves the outcome; throwing or returning a rejected Promise can replace it.
- The executor passed to `new Promise(...)` runs synchronously. Promise reaction callbacks run asynchronously as microtasks.

```javascript
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

delay(100).then(() => console.log("Timer finished"));
```

**Promise vs. callback:** A callback is a function passed to another function. A Promise standardizes eventual completion and chaining with error propagation. Promises do not automatically create threads, make CPU-heavy work nonblocking, or cancel an operation.

| Combinator | Result / use |
|---|---|
| `Promise.all(tasks)` | All fulfillment values in input order; rejects when one rejects. Does not cancel other operations. |
| `Promise.allSettled(tasks)` | Every outcome, including failures; useful for partial results. |
| `Promise.race(tasks)` | Adopts the first settlement, success or failure. |
| `Promise.any(tasks)` | First fulfillment; rejects with `AggregateError` if all reject. |

The operations often start when their functions are called; `Promise.all` coordinates their results. For thousands of requests, limit concurrency rather than starting everything at once.

### Async/await and error handling

**Interview answer:** `async` makes a function return a Promise. `await` pauses that async function's continuation until the awaited value settles; it does not block the browser's JavaScript thread while waiting. A rejected awaited Promise throws at the await point and can be handled with `try/catch`.

```javascript
async function loadJSON(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function loadDashboard() {
  try {
    const [events, profile] = await Promise.all([
      loadJSON("/api/events"),
      loadJSON("/api/profile"),
    ]);
    return { events, profile };
  } catch (error) {
    console.error("Dashboard request failed", error);
    throw error; // Let the UI caller show its error state.
  }
}
```

The two requests are independent, so both start before the await. If request B needs the ID from A, await A first. Two sequential independent requests cost roughly the sum of their latencies; concurrent ones roughly the slower latency, subject to networking/resource limits.

**Traps:**

- `fetch` generally fulfills for HTTP 404/500; inspect `response.ok`. Network failures and aborts can reject it.
- `try { loadJSON(url); } catch { ... }` does not catch a later rejection. Await the Promise inside the try or attach `.catch()`.
- `await` on a plain value still defers the following continuation; it does not convert CPU work into a background job.
- `forEach(async item => …)` does not await its callbacks. Use `for...of` for serial processing or `Promise.all(items.map(...))` for concurrent results.
- Async code runs synchronously until its first await; a heavy loop before or after await can still freeze the page. Consider a Web Worker for substantial CPU work.

See [MDN async functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function).

### Event loop and output questions

**Interview answer:** JavaScript executes the current call stack first. In a browser, when the stack empties at a microtask checkpoint, queued microtasks such as Promise continuations run before the next task, such as an eligible timer callback. The browser also schedules rendering opportunities; a timer delay is not an exact execution time.

```javascript
console.log("A");
setTimeout(() => console.log("B"), 0);
Promise.resolve().then(() => console.log("C"));
console.log("D");
// A, D, C, B
```

```javascript
async function example() {
  console.log("1");
  await Promise.resolve();
  console.log("2");
}
example();
console.log("3");
// 1, 3, 2
```

A chain that continually enqueues microtasks can delay rendering and other tasks. Async I/O lets the host handle waiting; it does not imply JavaScript callbacks execute in parallel on the same main thread.

### JavaScript fundamentals

| Question | Short answer / example |
|---|---|
| `var`, `let`, `const`? | `var` is function-scoped; `let`/`const` are block-scoped and have a temporal dead zone. `const` prevents reassignment, not mutation of an object. |
| `==` vs. `===`? | `==` allows type coercion; `===` does not. Prefer explicit conversion and strict equality. |
| What is a closure? | A function retains access to its lexical environment after the outer call returns; useful for callbacks and private state. |
| What is a stale closure? | A callback reads an older captured value; in React, examine dependencies, functional updates, and which render created the callback. |
| Shallow copy? | `{...object}` and `[...array]` copy one level. Nested objects remain shared references. |
| `null` vs. `undefined`? | `undefined` commonly indicates missing/uninitialized values; `null` is an explicit empty value. Both can be intentional. |
| Event propagation? | Capture travels toward the target, then bubbling travels toward ancestors for bubbling events. |
| Event delegation? | Handle child interactions on an ancestor using propagation; distinguish `event.target` from `event.currentTarget`. |
| `preventDefault` vs. `stopPropagation`? | The first cancels a cancelable default browser action; the second stops further propagation. Neither substitutes for the other. |
| Debounce vs. throttle? | Debounce waits for a quiet interval (search input); throttle limits frequency over time (scroll handling). |
| Arrow function vs. ordinary function? | An arrow captures lexical `this`; an ordinary function's `this` depends on how it is called. Arrows are not constructors. |

**Closure output question:** `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i), 0)` prints 3 three times because callbacks share one binding. Replacing `var` with `let` gives each iteration its own binding and prints 0, 1, 2.

### HTML, CSS, and accessibility

| Question | Interview answer |
|---|---|
| Semantic HTML? | Use elements that describe meaning: headings, navigation, forms, labels, buttons. This supports accessibility and browser behavior. |
| CSS box model? | Content, padding, border, margin. With `box-sizing: border-box`, declared width includes content, padding, and border, but not margin. |
| Flexbox vs. Grid? | Flexbox organizes a primary axis; Grid explicitly coordinates rows and columns. Choose based on the layout. |
| Specificity? | Within relevant cascade precedence, selectors have different specificity; ties can resolve by source order. `!important`, layers, and origins mean specificity alone is not the whole cascade. |
| Responsive layout? | Flexible sizing, appropriate layouts, media/container queries, and testing narrow screens and zoom. |
| Accessible form? | Associated labels, keyboard operation, visible focus, useful validation, and appropriately announced status/error messages. |

**Why a button rather than a clickable div?** A native button supplies semantics, keyboard behavior, focus handling, and disabled behavior. Adding `onClick` alone to a div does not recreate those capabilities. Use links for navigation and buttons for actions.

**Browser rendering pipeline:** A useful simplified model is parse HTML → DOM, parse CSS → style information, calculate styles and layout, paint, and composite. Updates may repeat parts of this pipeline. Repeated layout reads mixed with DOM writes can cause unnecessary synchronous layout; batch work and measure with browser tools.

### Browser storage and security

Browser storage lifetime and policy can be affected by privacy settings, browser restoration, and user actions. These concepts apply to both Angular and React. Related server-side protocols are in [authentication](../System_Design/Authentication_Authorization.md).

#### Local storage vs. session storage vs. cookies?

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

#### Where should a JWT be stored?

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

#### What do HttpOnly, Secure, and SameSite actually do?

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

#### XSS vs. CSRF vs. CORS?

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

#### How should refresh, reload, logout, and multiple tabs work?

Define access-token lifetime, server session lifetime, refresh rotation, and revocation separately. Coordinate concurrent refreshes so two tabs do not accidentally invalidate one another's token family. A stolen refresh token may outlive a short access token unless rotation/reuse detection and expiry are designed.

Logout should invalidate the server session/refresh capability, clear matching cookies correctly, and clear client state. An already issued access token can remain valid until expiry unless the verifier consults additional revocation state.

**Scenario:** user logs out in tab A but tab B still displays old data. Broadcast a logout notification where appropriate, but enforce access at the server rather than relying on tab coordination. Do not transmit raw credentials in cross-tab messages.

**Dig deeper:** how do you avoid an infinite refresh loop? What if refresh succeeds but the response is lost? Do you require reauthentication for sensitive actions?

##### How is login available in the next tab without exposing a JWT to JavaScript?

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

##### Multi-tab refresh and logout: practical rules

| Event | Browser/app behavior | Server enforcement |
|---|---|---|
| Open another tab | Load `/session` or obtain a tab-local access token through the supported flow | Validate the existing session; do not trust cached UI identity |
| Several requests expire together | Single in-flight refresh in a tab; use supported cross-tab locking if needed | Atomically manage rotation/session state; coordinate BFF replicas |
| Logout in tab A | Clear sensitive UI/draft state as policy requires; notify other tabs | Revoke session/refresh grant and expire the correct cookie |
| Tab B misses logout message | Recheck on resume or next request | Reject revoked session; previously issued JWTs need expiry or additional revocation checks |
| User signs into a different account | Invalidate stale UI caches and bind drafts to the correct account | Recheck ownership; never submit a prior user's draft under a new identity automatically |

`BroadcastChannel` or storage events can carry messages such as `logged-out` or `session-changed`, not raw credentials. They are UI coordination, not authorization. A cross-tab lock alone does not hand a new in-memory access token to every waiting tab; after obtaining the lock, each tab must recheck/bootstrap its own state through the supported architecture. A BFF simplifies this because token refresh happens behind the shared server session.

**Interview answer:** “I can share login across tabs using a host-scoped Secure HttpOnly cookie. JavaScript does not need to read it; the browser attaches it to eligible requests. A BFF keeps OAuth tokens server-side. I still protect against CSRF and XSS and enforce expiry and logout on the server.”

For the complete one-hour form timeline, retry/idempotency rules and refresh failure handling, see [long-form refresh](../System_Design/Authentication_Authorization.md#what-happens-during-a-one-hour-form).

#### How would you explain your design in an interview?

“I would first identify client and deployment constraints. For a same-origin browser app, I would evaluate a backend session/BFF and Secure HttpOnly cookie with CSRF protection. If the app must manage OAuth tokens, I would explain token lifetime and XSS exposure, keep refresh handling deliberate, and avoid claiming any storage mechanism eliminates browser compromise.”

This is a design example, not a claim that you implemented it. Use your actual project architecture when describing experience.

**Verify:** test malicious origins, expired sessions, role changes, simultaneous refresh, logout/relogin, cookie scope, and unauthorized record access. Inspect browser network/storage tools without recording live credentials in screenshots or logs.

### Practical frontend scenarios

#### Search results appear for an older query. What happened?

Requests can finish out of order. Debounce to reduce requests; cancel obsolete requests where possible and guard against outdated results. Debouncing alone does not solve the race. Represent loading, empty, success, and error states explicitly.

#### A user clicks Save twice. How do you prevent duplicates?

Disable/restrict repeated submission in the UI and show progress. Enforce idempotency or relevant uniqueness/transaction rules on the backend. A browser timeout does not prove the server did nothing; retries need deliberate semantics.

#### A page is slow. What do you investigate?

Separate network latency, bundle loading, JavaScript execution, React rendering, layout/paint, and oversized lists. Use network and performance profiling. Consider pagination/virtualization for large lists, smaller bundles, and fewer redundant requests; memoize only when profiling supports it.

#### How do you test a frontend component?

Test observable behavior: keyboard/user interactions, validation, loading/errors, correct submission, and late responses after inputs change. Mock network boundaries for focused tests and cover important flows end to end. Avoid tests tied only to internal state names or component implementation.

#### Can hiding a button enforce permissions?

No. UI checks improve usability; the server must authenticate and authorize every relevant operation and object. Follow the [browser storage/security guide](Frontend_Angular_React.md#browser-storage-and-security) and [authentication guide](../System_Design/Authentication_Authorization.md) for cookies, CORS, CSRF, XSS, and login flows.

#### How can I connect this to my project experience?

Use EventOps as a domain example: components for filters, availability, booking forms, and report status; API calls to Django/Flask; asynchronous loading/error handling. These are illustrative component boundaries. Your career materials confirm Angular/JavaScript authentication flows, visualization dashboards, and error handling. The exact screens, implementation details, and project-specific boundaries still need your own account. Explain the screens and code you actually worked on, and distinguish that experience from how you would design a new screen.

### Fundamentals revision and practice

Explain DOM/tree structure, framework tradeoffs, component boundaries, pure functions, Promises, async/await, and event-loop ordering before reading the answers. Then work through accessibility and request-race scenarios.

**Mock questions:** Why is the DOM not a binary tree? When would plain JavaScript be sufficient? Does await block the UI? How do you run independent requests concurrently? Why does debounce alone not prevent stale results? Why must the server prevent duplicate writes and enforce permissions?

**Coding drills:** Implement debounce; compare sequential and concurrent fetches; build an accessible form; handle loading/error/empty states and outdated responses. Use definition → example → tradeoff or trap for spoken answers.

### Fundamentals references

- [MDN: DOM](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model)
- [MDN: Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN: async functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN: microtasks](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)
- [MDN: accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility)
- [OWASP HTML5 security](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OAuth security best current practice](https://www.rfc-editor.org/rfc/rfc9700.html)

## Angular

Your career materials confirm Angular/JavaScript feature work on authentication, dashboards, and error handling. The APIs and exact screen implementations still need your own examples. Separate the Angular version you used historically from the modern APIs below; standalone components, signals, and newer template control flow may not have existed in that version.

| Question | Interview answer |
|---|---|
| Angular component? | A TypeScript class with component metadata, a template, and associated styling/behavior. Components compose a screen. |
| Data binding? | Interpolation displays expressions; property binding sends values to properties; event binding handles events; two-way binding combines value flow and change notification. |
| Dependency injection? | Angular supplies dependencies through configured providers, helping separate services from UI behavior and supporting testing. |
| Service vs. component? | Components own UI concerns; services can hold shared business/data-access behavior. Service scope depends on provider configuration. |
| Lifecycle hooks? | Examples include `ngOnInit` for initialization and `ngOnDestroy` for cleanup. These are a different API from React Hooks. |
| Promise vs. Observable? | A Promise has one eventual settlement. An Observable represents a subscription-based stream that may emit multiple values; cancellation behavior depends on its producer. |
| Angular HttpClient? | Commonly returns RxJS Observables; requests are sent on subscription, and separate subscriptions can cause separate requests. |
| Signals? | Reactive values that track consumers; computed signals derive values. Exact APIs and recommended patterns depend on Angular version. |

**Binding examples:** `{{ event.name }}`, `[disabled]="busy"`, `(click)="book()"`. A forms-based two-way example is `[(ngModel)]="name"`, requiring the appropriate forms support/imports.

**React vs. Angular:** React centers on UI components and Hooks with ecosystem choices around them. Angular provides an integrated framework with templates, dependency injection, routing, forms, and other facilities. Neither choice removes the need to understand JavaScript, DOM behavior, accessibility, or HTTP. See [Angular components](https://angular.dev/essentials/components).

### TypeScript: what does it add to JavaScript?

**Interview answer:** TypeScript checks types before execution and adds syntax for describing data contracts. Types are generally erased when compiled to JavaScript; an HTTP response still needs runtime validation when its contents are untrusted.

| Question | Answer / trap |
|---|---|
| Interface vs. type alias? | Both describe shapes; interfaces support declaration merging, while aliases can express unions and other type expressions. Choose based on the contract. |
| `any` vs. `unknown`? | `any` bypasses many checks; `unknown` requires narrowing before use. Prefer `unknown` at uncertain boundaries. |
| Union and narrowing? | `string \| null` permits either; a null check narrows the value before string operations. |
| Optional property? | `name?: string` may be absent; handle that possibility rather than adding a non-null assertion to silence it. |
| Does `http.get<Event[]>(...)` validate JSON? | No. The generic describes an expected type; it does not validate the server response at runtime. |

### How do components communicate?

Parents pass inputs; children emit outputs for actions. Use a shared service/store for unrelated components when lifting state to a common parent is insufficient. Avoid changing a parent's input object inside a child.

Classic syntax, useful for discussing older Angular applications:

```typescript
import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-event-card',
  standalone: true,
  template: `<button (click)="selected.emit(eventId)">{{ name }}</button>`,
})
export class EventCardComponent {
  @Input() eventId = '';
  @Input() name = '';
  @Output() selected = new EventEmitter<string>();
}
```

The parent binds `[eventId]`, `[name]`, and `(selected)`. Modern Angular also supplies signal-based input/output APIs. An Angular output is not automatically a bubbling native DOM event. Match the API to your deployed version.

### Constructor vs. ngOnInit vs. ngOnChanges?

The constructor creates the class and supports dependency injection; inputs are not yet initialized there. `ngOnChanges` reacts to input changes, including the first assignment before `ngOnInit`. `ngOnInit` runs once after initial inputs are set. Use `ngAfterViewInit` when initialization needs the component's initialized view and `ngOnDestroy` for owned-resource cleanup. Repeated mutation during change checking can cause errors or unnecessary work. See [Angular lifecycle](https://angular.dev/guide/components/lifecycle).

### Is a service always a singleton?

No. A root-provided service is generally shared within the application's root injection scope. A component-level provider creates an instance associated with that component's injector. Lazy/environment injector boundaries also affect scope. Explain where the provider is registered before claiming two components share one instance.

### Standalone components vs. NgModules?

Standalone components declare their template dependencies through imports without needing declaration in an NgModule. NgModules organize declarations/imports/providers in module-based applications. Both appear in real codebases; migration should preserve template dependencies and provider scope. Standalone does not mean every component is loaded lazily.

### Reactive forms vs. template-driven forms?

Reactive forms define an explicit form model in TypeScript and suit complex validation, dynamic controls, and direct testing. Template-driven forms express much of their setup through template directives and can suit simpler forms. Both need accessible labels, helpful errors, and server-side validation.

```typescript
import { FormControl, FormGroup, Validators } from '@angular/forms';

const bookingForm = new FormGroup({
  title: new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, Validators.maxLength(100)],
  }),
});

bookingForm.controls.title.setValue('Engineering meetup');
if (bookingForm.invalid) bookingForm.markAllAsTouched();
```

A component template using `[formGroup]`/`formControlName` needs `ReactiveFormsModule`. `setValue` requires the expected structure; `patchValue` updates supplied fields. Put validation involving several controls on their group. Debounce remote validation as appropriate, handle pending/error states, and validate again on the server. See [reactive forms](https://angular.dev/guide/forms/reactive-forms).

### Promise vs. Observable, and which RxJS operator should I choose?

A Promise settles once. An Observable can emit zero or more values and supports subscription teardown. Angular HTTP Observables normally start a request on subscription; multiple subscriptions can issue multiple requests. Unsubscription can abort an in-flight client request but cannot undo a server-side write. Not all Observables are cold or finite.

| Operator | Behavior | Typical choice / trap |
|---|---|---|
| `map` | Transform each emitted value | It does not subscribe to an inner HTTP Observable |
| `switchMap` | Switch to the newest inner stream; unsubscribe the previous one | Search queries; avoid for writes that must all complete |
| `concatMap` | Process inner streams sequentially | Ordered writes; queued work can grow |
| `mergeMap` | Subscribe concurrently, optionally with a concurrency bound | Independent work; completion order can vary |
| `exhaustMap` | Ignore new source values while the inner stream is active | Ignore repeated submit clicks; backend duplicate protection remains necessary |
| `catchError` | Replace or rethrow a stream error | Placement determines whether one request or the whole outer stream ends |

Service/component fragment; `this.http` is an injected `HttpClient`. Consume `results$` with one `AsyncPipe` subscription in the view (and import the pipe), or manage teardown explicitly:

```typescript
import { FormControl } from '@angular/forms';
import { catchError, debounceTime, distinctUntilChanged, map,
         of, startWith, switchMap } from 'rxjs';

interface EventSummary { id: string; name: string; }

// Inside the class, after the injected HttpClient is initialized:
query = new FormControl('', { nonNullable: true });
results$ = this.query.valueChanges.pipe(
  startWith(''),
  map(value => value.trim()),
  debounceTime(250),
  distinctUntilChanged(),
  switchMap(q => this.http.get<EventSummary[]>('/api/events', {
    params: { q },
  }).pipe(
    map(items => ({ items, error: '' })),
    catchError(() => of({ items: [] as EventSummary[], error: 'Search failed' })),
  )),
);
```

`switchMap` prevents an older active inner request from later emitting into this stream after a new debounced query is emitted. A new keystroke still waits for the debounce interval; this example does not immediately invalidate displayed results on every keypress. Production UI should represent the current query, loading, empty, and error states deliberately. Catching inside `switchMap` lets later queries continue after one HTTP error. See [HTTP request behavior](https://angular.dev/guide/http/making-requests).

### How do you prevent subscription leaks?

Prefer `AsyncPipe` for view subscriptions. For imperative subscriptions, use a supported lifetime helper such as `takeUntilDestroyed` in modern Angular, or an explicit destroy signal and `takeUntil` in older code. Long-lived form/route/event streams need cleanup; HTTP streams usually complete, but stale responses and unnecessary requests still matter. Nested subscriptions make cancellation and error flow harder to control; compose operators instead.

### What are interceptors, and how should auth errors work?

Interceptors apply cross-cutting HTTP behavior such as trusted-API auth headers, error mapping, and timing. Clone immutable request objects when changing headers. Restrict credentials to intended API destinations. A 401 may require a bounded session refresh or login; a 403 generally indicates denied access, not a reason for an infinite refresh loop. Coordinate concurrent refresh attempts, propagate failure, and avoid blindly retrying side-effecting writes. See [Angular interceptors](https://angular.dev/guide/http/interceptors).

### Guards, resolvers, and lazy routes?

Guards decide whether client navigation may proceed; they do not enforce server authorization. A guard can return a redirect representation rather than imperatively navigating and returning success. A resolver obtains route data before activation, which can simplify the component but delay navigation. Lazy routes defer loading route code; handle loading/failure states and consider preloading based on actual usage. See [route guards](https://angular.dev/guide/routing/route-guards).

### Change detection, OnPush, and signals?

Change detection checks bindings and updates the view. `OnPush` can skip eligible subtrees, but input changes are not its only trigger: handled events, notifications such as `AsyncPipe`, signal dependencies, and explicit marking can schedule work. Mutating an input object without changing its reference can leave an eligible child unchecked. Prefer explicit state updates and profile before optimizing. Signals hold reactive values; computed signals derive values, while effects serve external synchronization rather than routine derived state. Do not assume a particular Zone.js or zoneless setup across Angular versions. See [OnPush behavior](https://angular.dev/best-practices/skipping-subtrees).

### How do lists, pipes, and directives affect rendering?

Track rows by a stable business ID (`track` in modern `@for`, or `trackBy` in older `*ngFor`) so reordering can preserve DOM identity. A pure pipe recalculates when its primitive input or object reference changes; mutation within the same reference may not trigger it. Attribute directives change behavior/appearance; structural directives change view structure. Modern `@if`/`@for` are template control-flow syntax, not custom structural directives. Avoid expensive function calls in frequently checked bindings.

### How would you test authentication, dashboards, and error handling?

Test visible behavior: invalid forms do not submit, successful login updates the UI, denied APIs show an appropriate error, and an older search result does not overwrite the newest one. Use Angular `TestBed` for configured component/service tests and HTTP testing support to control responses. Verify requests, expected errors, teardown, and keyboard behavior. Keep important browser flows end to end; a mocked HTTP success does not establish that real login/cookie/CORS behavior works.

**Angular mock interview:** Explain an authentication feature you built; trace a dashboard request through a service and interceptor; choose a form strategy; diagnose duplicate HTTP requests; compare `switchMap` with `concatMap`; explain how you cleaned up a subscription; describe the Angular version and one test you wrote.

### Angular revision and practice

Practice component communication, lifecycle, provider scope, forms, RxJS operator choice, teardown, interceptors, guards, and change detection. Connect one authentication flow and one dashboard to code you actually wrote; name your historical Angular version.

**Coding drills:** Create a validated reactive form; wire a debounced HTTP search with `switchMap`; handle a failed request without ending future searches; test an authentication error and subscription cleanup.

### Angular references

- [Angular: components](https://angular.dev/essentials/components)
- [Angular: HTTP requests](https://angular.dev/guide/http/making-requests)
- [Angular: lifecycle](https://angular.dev/guide/components/lifecycle)
- [Angular: reactive forms](https://angular.dev/guide/forms/reactive-forms)
- [Angular: interceptors](https://angular.dev/guide/http/interceptors)
- [Angular: guards](https://angular.dev/guide/routing/route-guards)
- [Angular: OnPush](https://angular.dev/best-practices/skipping-subtrees)

## React

Function-component examples use JSX and require a React setup. Review the [shared fundamentals](#fundamentals) before the Hooks and effect questions.

### React component example

```jsx
import { useState } from "react";

function BookingButton({ eventName, onBook }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleClick() {
    setBusy(true);
    setError("");
    try {
      await onBook();
    } catch {
      setError("Booking failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button disabled={busy} onClick={handleClick}>
        {busy ? "Booking…" : `Book ${eventName}`}
      </button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
```

`eventName` and `onBook` are inputs (props); `busy` and `error` are local state. The parent supplies booking behavior. Disabling the button improves UX; the server must still prevent duplicate bookings.

A React component is not the same mechanism as a browser Web Component/custom element.

### Props, state, rendering, and keys

| Question | Interview answer |
|---|---|
| Props vs. state? | Props are read-only inputs from a parent; state is component-managed memory that can request a new render. |
| What is rendering? | React calls components to calculate the next UI description; the commit phase applies needed changes. Rendering does not imply every DOM node changes. |
| Why not mutate state? | React state should be treated as immutable snapshots. Create a new object/array so updates are explicit and previous snapshots remain intact. |
| What triggers rendering? | State updates, ancestor rendering, and subscribed context/external-store changes are common causes; optimizations may skip work. |
| What are keys? | Stable sibling identities that help React match items across insertions, deletion, and reordering. |
| Controlled input? | Its value is driven by state and updated through an input handler. An uncontrolled input keeps its current value in the DOM. |
| Lifting state up? | Put shared state in the nearest common owner and pass values and callbacks to children. |

```jsx
setItems(previous => [...previous, newItem]);
setCount(previous => previous + 1);
// In JSX: items.map(item => <Row key={item.id} item={item} />)
```

A state setter requests another render; it does not rewrite the variable in the current handler. If `count` is 0, calling `setCount(count + 1)` twice in the same handler typically requests 1 twice. Calling the functional updater twice produces 2. Closures capture the values associated with their render. See [React state snapshots](https://react.dev/learn/state-as-a-snapshot).

Avoid random keys or array indexes for reorderable lists: identity changes can reset input state or associate it with the wrong item. `key` is not passed as a normal prop; pass an explicit ID if the child needs it.

### What are React Hooks?

**Interview answer:** Hooks are functions that let function components use React features such as state, context, refs, and effect synchronization. Custom Hooks package reusable stateful logic.

| Hook | Purpose | Common trap |
|---|---|---|
| `useState` | Local state that can trigger rendering | Mutating objects or assuming the current variable changes immediately |
| `useReducer` | State transitions described by actions and a reducer | Putting side effects inside the reducer |
| `useContext` | Read and subscribe to a context value | Treating context as a complete server-data cache |
| `useRef` | Retain a mutable value or reference a DOM node | Expecting a ref write to trigger rendering |
| `useEffect` | Synchronize with an external system after commit | Using it for every derived value or omitting dependencies |
| `useLayoutEffect` | Layout-related synchronization before browser repaint | Blocking paint unnecessarily; use ordinary effects when suitable |
| `useMemo` | Cache a calculated result while dependencies match | Treating caching as necessary for correctness |
| `useCallback` | Cache a function identity while dependencies match | Assuming it makes executing the function faster |

**Rules:** Call these Hooks at the top level of React components or custom Hooks, before conditional returns. Do not call them in loops, conditions, event handlers, or ordinary utility functions. Consistent call order lets React associate Hook calls with their stored state. React's separate `use` API has special rules; do not generalize that exception to `useState` or `useEffect`.

**Custom Hook:** A function named `useSomething` that composes Hooks. It shares logic, not automatically shared state: two calls to a local-state Hook have separate state unless they connect to a shared store/context.

**Ref vs. state:** Use state for values that affect displayed output. Use refs for values such as timer IDs or DOM handles that must persist without requesting a render. Measure performance before introducing memoization.

### Side effects in React

React rendering should be pure because React may repeat or abandon render work. Put user-triggered actions such as a purchase request in an event handler. Use an Effect when the rendered component must stay synchronized with something external, such as a connection or subscription.

**Side effect vs. useEffect:** Side effect is a general programming concept; `useEffect` is one React API. Not every side effect belongs inside `useEffect`. Derived display values such as a filtered list can usually be calculated during rendering.

### How does useEffect work?

**Interview answer:** `useEffect` synchronizes a component with an external system. It runs setup after a commit; when dependencies change, React runs the previous cleanup before the next setup. Cleanup also runs when the component unmounts.

| Dependency argument | Behavior |
|---|---|
| Omitted | Runs after each relevant component commit |
| `[]` | No reactive dependencies; setup on mount and cleanup on unmount, with additional development checks possible |
| `[roomId]` | Setup on mount and again when `roomId` changes using `Object.is` comparison |

Include every reactive value read by setup/cleanup. Do not remove dependencies just to silence a loop. An object/function created during every render has a new identity, which can cause repeated synchronization.

```jsx
import { useEffect, useState } from "react";

function EventDetails({ eventId }) {
  const [result, setResult] = useState({ loading: true, data: null, error: "" });

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setResult({ loading: true, data: null, error: "" });

    async function load() {
      try {
        const response = await fetch(`/api/events/${encodeURIComponent(eventId)}`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (active) setResult({ loading: false, data, error: "" });
      } catch (error) {
        if (active) {
          setResult({ loading: false, data: null, error: "Could not load event." });
        }
      }
    }

    load();
    return () => {
      active = false;
      controller.abort();
    };
  }, [eventId]);

  if (result.loading) return <p role="status">Loading…</p>;
  if (result.error) return <p role="alert">{result.error}</p>;
  return <h2>{result.data.name}</h2>;
}
```

Cleanup cancels the browser operation where supported and prevents obsolete results from updating this effect's state. It does not undo work already processed by the server. Route loaders or a query library can additionally handle caching, deduplication, and retries; this snippet illustrates lifecycle mechanics.

**Why not `useEffect(async () => …)`?** An async function returns a Promise; React expects the setup to return a cleanup function or nothing. Define and call an async function inside the setup.

**Why twice in development?** Strict Mode can run an extra setup → cleanup → setup cycle to expose missing cleanup. Make synchronization resilient; do not assume `[]` means exactly one request forever. Remounting also runs setup again.

**Infinite loop?** An Effect updates state, that update changes a dependency, and setup repeats. First check whether the value can be derived during rendering instead. For subscriptions/timers, remove the listener or clear the timer in cleanup.

See [React useEffect](https://react.dev/reference/react/useEffect) for dependency and lifecycle details.

### React revision and practice

Practice props/state, render versus commit, stable keys, Hooks, state snapshots, refs, functional updates, effect dependencies, and cleanup.

**Mock questions:** Where should shared state live? Why must ordinary Hooks keep a consistent call order? When should a value be a ref? Why can an Effect run setup again? Which actions belong in event handlers? How would you prevent obsolete fetch results updating a component?

**Coding drills:** Build a controlled counter/search input; extract a custom Hook; explain a stale closure; add effect cleanup; compare a derived render value with unnecessary effect-managed state.

### React references

- [React: your first component](https://react.dev/learn/your-first-component)
- [React: Hooks reference](https://react.dev/reference/react/hooks)
- [React: rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)
- [React: state as a snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React: useEffect](https://react.dev/reference/react/useEffect)
- [React: you might not need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
