# Spring Boot Interview Cheat Sheet

Practical senior-level questions: explain what happens at runtime, choose a boundary, show syntax, and defend failure behavior. Examples target Java 17+ with Spring Boot 3.x / Spring Framework 6 conventions (`jakarta.*`, bean-based security). Boot 4 / Framework 7 can change packages, dependencies, defaults, and testing setup; use your project's dependency BOM and matching documentation. Snippets omit imports and application-specific collaborators.

Related: [Java](Java.md), [OOP](OOP.md), [Database](Database.md).

## Contents

- [Startup and dependency injection](#startup-and-dependency-injection)
- [Proxies, transactions, and async](#proxies-transactions-and-async)
- [REST APIs and security](#rest-apis-and-security)
- [JPA and database performance](#jpa-and-database-performance)
- [Reliability and distributed workflows](#reliability-and-distributed-workflows)
- [Testing and production diagnosis](#testing-and-production-diagnosis)
- [References](#references)

## Startup and dependency injection

### 1. What does Spring Boot do beyond Spring?

Spring supplies DI, AOP, transactions, MVC, and other programming infrastructure. Boot assembles defaults through auto-configuration, dependency management/starters, executable applications, and operational integration. A starter brings dependencies; auto-configuration creates eligible infrastructure beans.

```java
@SpringBootApplication
public class OrdersApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrdersApplication.class, args);
    }
}
```

`@SpringBootApplication` combines Boot configuration, component scanning, and auto-configuration. Put it in a sensible root package. Startup broadly prepares the environment/context, registers definitions, instantiates and post-processes non-lazy singletons, and starts infrastructure. Exact event ordering depends on the application type.

**Dig deeper:** why does moving the main class break bean discovery? How does defining a custom bean change an auto-configured default? Why can adding a dependency change startup behavior?

### 2. How does auto-configuration decide what to create, and how do you debug it?

Conditions examine available classes, existing beans, properties, and application type. For example, an eligible data source auto-configuration can back off when an application supplies its own `DataSource`.

```java
@Configuration(proxyBeanMethods = false)
class ClientConfiguration {
    @Bean
    @ConditionalOnMissingBean(PaymentClient.class)
    PaymentClient paymentClient(PaymentProperties properties) {
        return new PaymentClient(properties.baseUrl());
    }
}
```

**Practical diagnosis:** inspect the condition evaluation report (`--debug`), effective configuration, classpath, and bean definitions. Use explicit configuration when defaults no longer match; exclude a specific auto-configuration only when you understand what replaces it. See [Boot auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html).

**Dig deeper:** with `proxyBeanMethods=false`, direct calls to another `@Bean` method are normal Java calls. Inject dependencies as method parameters instead of relying on intercepted calls.

### 3. How do you choose an implementation and avoid hidden dependencies?

```java
@Service
class CheckoutService {
    private final PaymentGateway gateway;
    CheckoutService(@Qualifier("cardGateway") PaymentGateway gateway) {
        this.gateway = gateway;
    }
}
```

A single constructor does not need `@Autowired`. `@Primary` supplies a default among candidates; `@Qualifier` narrows selection for a particular injection point. `@Component`, `@Service`, and `@Repository` express roles; `@Bean` is useful for explicit construction, especially third-party classes. Repository exception translation requires the appropriate infrastructure.

| Choice | Benefit | Tradeoff |
|---|---|---|
| Constructor injection | Required dependencies visible; simple unit tests | Dependency cycles surface early |
| Field injection | Short declaration | Hidden construction requirements; awkward plain tests |
| `ObjectProvider<T>` | Deferred / repeated lookup when lifecycle requires it | More runtime resolution and framework coupling |

**Dig deeper:** fix a circular dependency by separating responsibilities or introducing orchestration; `@Lazy` can defer the cycle without fixing the design.

### 4. Are singleton beans thread-safe? What about injecting a prototype?

A Spring singleton is one instance per bean definition per container. It is not one per cluster and is not automatically thread-safe. Controllers/services should usually keep request state in method locals and use thread-safe collaborators.

```java
@Component
@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
class ExportSession { /* per-export mutable state */ }

@Service
class ExportService {
    private final ObjectProvider<ExportSession> sessions;
    ExportService(ObjectProvider<ExportSession> sessions) { this.sessions = sessions; }
    void export() {
        ExportSession session = sessions.getObject(); // request a fresh prototype
        // use and clean up this session
    }
}
```

Injecting a prototype directly into a singleton normally resolves it once, at singleton construction. Request-scoped proxies/providers can bridge scopes when an active request exists. Spring does not automatically run full destruction callbacks for prototype instances; the owner must arrange cleanup. See [bean scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html).

**Dig deeper:** what happens to request context on an async executor? Why should a field like `currentUser` never hold request-specific data in a singleton controller?

### 5. How do you manage configuration and secrets?

```java
@ConfigurationProperties(prefix = "payments")
@Validated
record PaymentProperties(@NotNull URI baseUrl, @Min(1) int maxAttempts) {}

@Configuration(proxyBeanMethods = false)
@EnableConfigurationProperties(PaymentProperties.class)
class PaymentsConfiguration {}
```

Use typed properties for related settings, validate them at startup, and supply secrets through an appropriate external secret/configuration mechanism. Profiles select environment-specific behavior; they are not a secret vault. Environment/command-line/test overrides can change effective values, so inspect property origins when a deployment behaves differently.

**Dig deeper:** how do you rotate credentials? Does the client rebuild when a value changes? Why should config/Actuator responses and logs avoid exposing secrets?

## Proxies, transactions, and async

### 6. Why does @Transactional sometimes do nothing?

In normal proxy mode, the caller must invoke an eligible method through the Spring proxy. Calling `this.save()` bypasses that proxy. Private methods cannot be advised through normal proxies; final methods cannot be overridden by class-based proxies. Objects constructed with `new` are outside container advice unless deliberately integrated.

```java
@Service
class OrderWriter {
    private final OrderRepository orders;
    OrderWriter(OrderRepository orders) { this.orders = orders; }

    @Transactional
    public void place(Order order) { orders.save(order); }
}
@Service
class CheckoutFacade {
    private final OrderWriter writer;
    CheckoutFacade(OrderWriter writer) { this.writer = writer; }
    public void checkout(Order order) { writer.place(order); } // through bean proxy
}
```

**Dig deeper:** JDK proxies expose interfaces; class-based proxies subclass the target. What does this imply for final classes and method visibility? Prefer public service boundaries for portable transaction behavior. The same self-invocation concern applies to common proxy-based caching and async advice.

### 7. When does a transaction roll back? Why did catching an exception change the outcome?

By default, Spring rolls back for unchecked exceptions and `Error`, not ordinary checked exceptions. Customize deliberately; configuration can alter defaults. If you catch a failure and return normally, advice may see success, although persistence failures can already have marked the transaction rollback-only.

```java
@Transactional(rollbackFor = IOException.class)
public void importOrders(Path path) throws IOException {
    // read and persist; exception crossing this boundary triggers the rule
}
```

`readOnly=true` is a transaction hint/optimization, not a universal write-prevention guarantee. `save()` need not execute SQL immediately; flush or commit can reveal constraints later. A transaction timeout does not reliably cancel every external call.

**Dig deeper:** why can outer commit throw `UnexpectedRollbackException` after an inner failure was caught? How do you test a commit-time failure rather than only a method return? See [transaction annotation semantics](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html).

### 8. REQUIRED vs. REQUIRES_NEW vs. NESTED?

| Propagation | Behavior | Practical cost / risk |
|---|---|---|
| `REQUIRED` | Join existing transaction, otherwise create one | Inner rollback-only can prevent outer commit |
| `REQUIRES_NEW` | Suspend outer; use an independent transaction | Extra connection demand; inner commit survives outer rollback |
| `NESTED` | Savepoint within an existing transaction, when supported | Transaction-manager/driver dependent; not independent durability |
| `NOT_SUPPORTED` | Suspend transaction for that scope | No atomicity with surrounding work |

```java
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void recordAttempt(Attempt attempt) { attempts.save(attempt); }
```

Invoke this on a separate proxied bean. An independent audit record can be intentional; an independent inventory update can break an order invariant. `NESTED` is not automatically supported by JPA transaction management.

**Dig deeper:** with every worker holding an outer connection and waiting for a second connection, how can `REQUIRES_NEW` exhaust a pool? Does isolation specified by a joining method change the existing transaction? Usually it does not; validate boundaries/settings deliberately.

### 9. How do @Async and transactions interact?

```java
@Configuration
@EnableAsync
class AsyncConfiguration {
    @Bean("notifications")
    Executor notifications() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(4);
        executor.setMaxPoolSize(8);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("notifications-");
        return executor; // Spring manages initialization and destruction
    }
}
@Service
class NotificationWorker {
    @Async("notifications")
    public CompletableFuture<Void> send(long orderId) {
        // load needed state inside this task; apply its own transaction if required
        return CompletableFuture.completedFuture(null);
    }
}
```

The caller's thread-bound transaction does not automatically cross into the worker. Self-invocation bypasses async advice. Choose bounded executors, rejection handling, shutdown policy, and observable failures. Void-returning async errors cannot be received as a caller result.

**Dig deeper:** why can an async task run before the caller commits? `@TransactionalEventListener(AFTER_COMMIT)` can coordinate local timing, but in-memory listeners do not guarantee crash-safe delivery. Use an outbox for durable work.

## REST APIs and security

### 10. What happens between an HTTP request and a controller?

In Servlet MVC, container filters (including Spring Security) run around the request; `DispatcherServlet` finds a handler, invokes interceptors/controller, and uses message conversion to read/write bodies. Exception resolvers translate eligible handler failures.

| Extension | Typical use | Boundary |
|---|---|---|
| Servlet filter | Correlation IDs, security infrastructure, request wrapping | Outside MVC handler logic |
| MVC interceptor | Handler-aware timing / request context | Does not replace security filters |
| AOP advice | Service-method concerns | Only advised invocations; not every HTTP failure |
| `@RestControllerAdvice` | Consistent MVC error responses | Security-filter errors need security handlers |

**Dig deeper:** where should authentication failure become 401? Why might a controller advice never see malformed requests rejected by an upstream gateway or security filter?

### 11. How do you validate requests and return safe errors?

```java
record CreateOrderRequest(@NotNull Long productId, @Min(1) int quantity) {}

@RestController
@RequestMapping("/orders")
class OrderController {
    private final OrderService service;
    OrderController(OrderService service) { this.service = service; }
    @PostMapping
    ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest body) {
        OrderResponse result = service.create(body);
        return ResponseEntity.created(URI.create("/orders/" + result.id())).body(result);
    }
}
@RestControllerAdvice
class ApiErrors {
    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail missing(OrderNotFoundException error) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, "Order not found");
    }
}
```

Use a validation implementation dependency. Add deliberate validation-error mapping for your API contract. Validate domain rules in the service/domain too; controllers are not the only callers. Return DTOs instead of serializing persistence entities and internal fields.

**Dig deeper:** 400 for invalid shape vs. 409 for a state conflict? How do you preserve correlation IDs without returning stack traces? An application `exists` check cannot replace a DB unique constraint under concurrency.

### 12. How do you secure endpoints and individual records?

```java
@Configuration
@EnableMethodSecurity
class SecurityConfiguration {
    @Bean
    SecurityFilterChain security(HttpSecurity http) throws Exception {
        return http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .oauth2ResourceServer(oauth -> oauth.jwt(Customizer.withDefaults()))
            .build();
    }
}
```

This requires resource-server/JWT support and issuer/key configuration. It leaves CSRF defaults intact; adapt the policy to credential transport and supported browser clients. URL authorization alone does not prove the caller owns a requested order: enforce tenant/owner predicates in the service/query.

| Concept | Purpose | Trap |
|---|---|---|
| Authentication | Establish identity | Parsing a JWT without verifying it is not authentication |
| Authorization | Decide permitted action/resource | Guessable IDs can expose other users' data |
| CSRF defense | Prevent forged browser requests using ambient credentials | Stateless servers can still be vulnerable when credentials are sent automatically |
| CORS | Browser cross-origin access policy | Not authentication or a general server-to-server access control |
| JWT | Locally verifiable token claims | Validate signature, issuer, expiry, audience as required; plan revocation/rotation |

**Dig deeper:** `hasRole("ADMIN")` conventionally checks `ROLE_ADMIN`. 401 means missing/invalid authentication; 403 means access denied for an authenticated caller, subject to deliberate resource-hiding policies. See [request authorization](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html).

## JPA and database performance

### 13. Why can one repository call produce hundreds of queries?

N+1 occurs when one query loads parents and additional queries load each relationship. It can appear during DTO mapping or serialization. Lazy loading postpones retrieval; eager fetching does not guarantee one SQL query.

```java
interface OrderRepository extends JpaRepository<Order, Long> {
    @EntityGraph(attributePaths = "customer")
    List<Order> findByStatus(OrderStatus status);
}
```

| Technique | Fit | Tradeoff |
|---|---|---|
| Fetch join / entity graph | Known relationships required by a use case | Collection joins multiply SQL rows; pagination needs care |
| DTO projection | API/report needs a subset of columns | Query-specific representation |
| Batch fetching | Load related values in groups | Extra queries remain; provider-specific tuning |
| Open persistence context through web rendering | Allows later lazy access | Hides DB access and may move queries outside intended boundaries |

Prefer DTO mapping within a deliberate transactional read boundary; consider `spring.jpa.open-in-view=false` for explicit boundaries. Verify SQL count and plans. For collection pagination, page root IDs first then fetch required associations; define ordering and consistency expectations.

**Dig deeper:** why is globally changing every relationship to EAGER a poor fix? Why can `LazyInitializationException` reveal a boundary problem rather than a request to enable OSIV?

### 14. How do you prevent lost updates or overselling?

```java
@Entity
class Inventory {
    @Id Long id;
    @Version long version;
    int available;
}

interface InventoryRepository extends JpaRepository<Inventory, Long> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select i from Inventory i where i.id = :id")
    Optional<Inventory> lockById(@Param("id") Long id);
}
```

Use the locking query inside a transaction. Optimistic version checks detect conflicts at flush/commit; pessimistic locks serialize access and can block/deadlock. Conditional SQL such as `UPDATE ... SET available=available-1 WHERE available>0` is often ideal for a single-row decrement; check affected rows.

| Option | Prefer when | Cost |
|---|---|---|
| Optimistic version | Conflicts uncommon | Retry or surface conflict; reload state before retry |
| Pessimistic row lock | Short, conflict-heavy critical sections | Waiting, deadlocks, timeout policy |
| Conditional update | Invariant fits one atomic statement | Persistence context may become stale after bulk updates |

**Dig deeper:** a version on one row does not protect a multi-row predicate such as “at least one doctor on call.” Choose locking/serializable isolation around the whole invariant. Never blindly retry an external payment as part of a DB retry.

### 15. Why is the connection pool full when CPU is low?

Requests may be holding connections during slow SQL, lock waits, long transactions, or remote calls. Pool size is a database concurrency limit, not a cure for slow queries. Budget the total across all application replicas and background jobs.

```properties
# Illustrative values, not universal tuning recommendations.
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.connection-timeout=1000
spring.jpa.open-in-view=false
```

**Investigate:** pool active/pending counts, acquisition time, DB activity/locks, transaction duration, query plans, and traffic. Bound waiting and downstream call timeouts. Virtual threads do not create more DB capacity.

**Dig deeper:** why can increasing every replica's pool degrade throughput? Separate connection acquisition timeout from SQL execution timeout and remote-call timeout.

### 16. How do you deploy schema changes safely?

Use versioned Flyway/Liquibase migrations; avoid relying on `ddl-auto=update` as production change management. Use expand/backfill/switch/contract for incompatible changes while old and new app versions coexist.

```properties
spring.jpa.hibernate.ddl-auto=validate
```

**Scenario:** add a required column by introducing a compatible nullable/default strategy, deploy writers, backfill in bounded batches, validate data, then enforce constraints and eventually remove compatibility code. Index builds and constraints need engine-specific lock analysis.

**Dig deeper:** what happens if migration succeeds but application deployment fails? Prefer forward-compatible migrations and rehearsed recovery. Does your migration tool wrap the operation in a transaction, and does that work with concurrent index creation?

## Reliability and distributed workflows

### 17. When should you cache, and what can go wrong?

```java
@EnableCaching
@Configuration
class CacheConfiguration {}

@Service
class ProductReader {
    @Cacheable(cacheNames = "products", key = "#id")
    public ProductDto find(long id) { return loadProduct(id); }
}
```

Configure a provider and expiry/size policy explicitly. Proxy interception applies; a local method call may bypass caching. Tenant, authorization, locale, and version can belong in the key. Cache DTOs/immutable values rather than managed entities.

| Cache | Benefit | Tradeoff |
|---|---|---|
| Local in-process | Very low latency | Different replicas can disagree; memory per replica |
| Shared Redis | Shared values and invalidation surface | Network/failure dependency and serialization |
| No cache | Freshness and fewer moving parts | Repeated DB/compute cost |

**Dig deeper:** stale cache fill can race with eviction; after-commit eviction helps timing but is not universal consistency. How do TTL jitter, per-key single-flight, and stale-while-revalidate reduce stampedes? What happens when the cache is down?

### 18. How do retries, timeouts, circuit breakers, and bulkheads differ?

See the shared [Circuit Breaker pattern](../System_Design/Design_Patterns.md#circuit-breaker) for state transitions and recovery behavior.

| Mechanism | Solves | Does not solve |
|---|---|---|
| Timeout | Bounds an attempt's waiting | Proof that remote work did not happen |
| Retry with backoff/jitter | Transient failures | Permanent errors; duplicate side effects |
| Circuit breaker | Avoid repeated calls during downstream failure | Enforce global concurrency capacity |
| Bulkhead | Isolate concurrency/resource budgets | Make the downstream healthy |
| Rate limit | Bound accepted traffic over time | Bound every in-flight slow operation |

Use a client/framework resilience library with explicit limits; Spring Boot alone does not automatically implement these policies. Bound the total request deadline and retry budget, and avoid retries at every layer multiplying attempts.

**Dig deeper:** a timeout after a charge is ambiguous; retry only with a stable idempotency key or query status. Which errors are retryable? What happens when all replicas enter retry together?

### 19. How do you prevent duplicate orders and reliably publish events?

A client-supplied operation key should map to a durable request/result record, scoped to tenant/user and operation. Enforce uniqueness in the database; store a payload fingerprint so reusing a key for different data is rejected.

```sql
CREATE TABLE checkout_requests (
    tenant_id BIGINT NOT NULL,
    request_key TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    order_id BIGINT,
    PRIMARY KEY (tenant_id, request_key)
);
```

Write the order and outbox event in one local transaction. A publisher sends committed outbox rows and marks progress. Crashes between send and marking can duplicate events; consumers must deduplicate using an event ID and commit deduplication with their own local effect.

**Dig deeper:** how do concurrent requests with the same key wait or return an in-progress result? Why is `@Transactional` around SQL plus a broker send not automatically one atomic transaction? How do you preserve per-order event ordering and recover stuck outbox rows?

## Testing and production diagnosis

### 20. Which test should you write?

Start with [JUnit lifecycle, assertions, and test doubles](Java.md#junit-lifecycle-assertions-and-test-doubles) for plain Java tests, then choose which Spring boundary needs integration coverage.

| Test | Purpose | Limitation |
|---|---|---|
| Plain unit test | Domain/service decisions with fakes | Does not exercise Spring advice or DB behavior |
| `@WebMvcTest` + MockMvc | Routing, validation, JSON, MVC/security behavior with configured collaborators | Narrow context; explicit security/auth setup matters |
| `@DataJpaTest` | Mapping and query behavior | Test DB may differ; rollback can hide commit-time failures |
| Real DB integration (e.g. Testcontainers) | Engine-specific SQL, locking, migration, constraints | Slower and needs container infrastructure |
| `@SpringBootTest` | Full application wiring / selected end-to-end flows | More setup and diagnostic cost |

MockMvc example inside a configured web test:

```java
mockMvc.perform(post("/orders")
        .with(csrf())
        .contentType(MediaType.APPLICATION_JSON)
        .content("{\"productId\":7,\"quantity\":0}"))
    .andExpect(status().isBadRequest());
// Supply an authenticated test principal when the endpoint requires one.
```

**Dig deeper:** direct unit calls do not verify `@Transactional`. Test race conditions with independent transactions/connections and deterministic coordination. Test duplicate keys, rollback, actual commit, and crash/retry boundaries where they matter.

### 21. How do you diagnose an incident and expose health safely?

Start with user symptoms and a recent-change timeline. Correlate request rate, error rate, latency, CPU/memory, GC, executor queues, and DB pool waits. Trace slow requests, inspect SQL and lock waits, and use profiles to confirm CPU/allocation bottlenecks.

| Signal | Use | Pitfall |
|---|---|---|
| Logs | Specific events with request/trace IDs | Secrets, excessive volume, missing cross-thread context |
| Metrics | Trends and alerts | User IDs/URLs as labels create high cardinality |
| Traces | Cross-service critical path | Sampling can omit rare failures |
| Liveness | Should process restart? | Depending on a shared DB can cause restart storms |
| Readiness | Should this instance receive traffic? | Dependency checks need deliberate fail-open/fail-closed policy |

Expose only required Actuator endpoints with appropriate network/security controls. Graceful shutdown stops accepting new work and gives in-flight work a bounded completion period; align orchestrator termination windows and background executor shutdown.

**Dig deeper:** what happens to a message being processed when the pod terminates? Which operations can safely be retried? Why can a health check succeed while p99 is terrible?

## References

- [Spring Boot auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)
- [Spring bean scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)
- [Spring AOP proxying](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)
- [Spring declarative transactions](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html)
- [Spring transaction propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)
- [Spring asynchronous execution](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)
- [Spring Data JPA query methods and entity graphs](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)
- [Spring Security request authorization](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html)
- [Spring Boot testing](https://docs.spring.io/spring-boot/reference/testing/index.html)
- [Spring Boot production features](https://docs.spring.io/spring-boot/reference/actuator/index.html)
