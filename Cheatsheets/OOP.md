# OOP Interview Cheat Sheet

Practical senior-level questions using Java syntax. Read alongside [Java](Java.md), [Spring Boot](SpringBoot.md), and [Database](Database.md). Examples are focused fragments with domain collaborators omitted. For every design, defend its invariant, extension points, failure handling, and testability.

## Contents

- [Pillars and domain invariants](#pillars-and-domain-invariants)
- [Interface vs. abstract class](#interface-vs-abstract-class)
- [Overloading, overriding, and dispatch](#overloading-overriding-and-dispatch)
- [Composition vs. inheritance](#composition-vs-inheritance)
- [SOLID under practical constraints](#solid-under-practical-constraints)
- [Patterns with tradeoffs](#patterns-with-tradeoffs)
- [Dependency injection and object lifecycle](#dependency-injection-and-object-lifecycle)
- [Design exercise: checkout](#design-exercise-checkout)
- [Refactoring and testing](#refactoring-and-testing)
- [References](#references)

## Pillars and domain invariants

### 1. What do encapsulation and abstraction mean beyond getters and setters?

**Scenario:** an account exposes `setBalance`, so any caller can create an invalid balance. Encapsulation means the object owns and protects its invariant. Abstraction offers a meaningful operation without exposing storage or implementation details.

```java
final class Account {
    private long balanceInCents;

    Account(long openingBalance) {
        if (openingBalance < 0) throw new IllegalArgumentException("negative balance");
        balanceInCents = openingBalance;
    }

    void debit(long cents) {
        if (cents <= 0 || cents > balanceInCents) {
            throw new IllegalArgumentException("invalid debit");
        }
        balanceInCents -= cents;
    }

    long balanceInCents() { return balanceInCents; }
}
```

This protects single-object sequential use; it does not coordinate concurrent threads, two accounts, or database transactions. Validate money units/currency and overflow in the actual domain.

**Dig deeper:** why isn't a private field plus a public setter sufficient? What happens if a mutable internal list is returned? Where should a rule involving multiple accounts live?

### 2. What do inheritance and polymorphism buy you?

Inheritance establishes a subtype relationship; polymorphism lets callers use a shared contract while implementations vary. The contract includes behavior and failure semantics, not just matching method signatures.

```java
interface ShippingPolicy {
    long feeInCents(long cartTotalInCents);
}
final class FreeOverThreshold implements ShippingPolicy {
    public long feeInCents(long total) { return total >= 5000 ? 0 : 499; }
}
final class Checkout {
    private final ShippingPolicy shipping;
    Checkout(ShippingPolicy shipping) { this.shipping = shipping; }
    long shippingFee(long total) { return shipping.feeInCents(total); }
}
```

**Dig deeper:** how would you add region-specific shipping? Is an interface necessary when there is only one stable implementation? Prefer a clear seam over speculative abstraction.

## Interface vs. abstract class

### 3. When would you choose each?

| Choice | Practical fit | Tradeoff |
|---|---|---|
| Interface | Contract across unrelated implementations; replaceable adapter | Shared mutable instance state is not provided; defaults can conflict |
| Abstract class | Closely related implementations sharing state and a stable algorithm | Uses the one class-inheritance slot; subclasses couple to protected behavior |
| Concrete class | One cohesive implementation with no variability need | Introduce a contract later if a real seam emerges |

```java
interface ReceiptSender {
    void send(Receipt receipt);
}
abstract class ReportExporter {
    public final byte[] export(Report report) {
        validate(report);
        return encode(report);
    }
    private void validate(Report report) { /* shared invariant */ }
    protected abstract byte[] encode(Report report);
}
```

**Dig deeper:** interfaces can contain default/static methods and private helpers; they are not limited to abstract declarations. If two interfaces supply the same default method, explicitly resolve the conflict. Why can calling an overridable method from a constructor observe incomplete subclass state?

## Overloading, overriding, and dispatch

### 4. Which method runs, and when is the decision made?

```java
class Parent {
    String kind(Object x) { return "parent-object"; }
    String label() { return "parent"; }
}
class Child extends Parent {
    String kind(String x) { return "child-string"; } // overload
    @Override String label() { return "child"; }
}
Parent p = new Child();
p.kind("hello"); // parent-object: overload selection uses static types
p.label();       // child: overridden instance method uses runtime receiver
```

| Mechanism | Selection | Interview trap |
|---|---|---|
| Overloading | Compile time, argument/receiver declared types | Return type alone cannot distinguish overloads |
| Overriding | Runtime dispatch after method selection | Cannot reduce access or broaden checked exceptions |
| Static method hiding | Declared type / class | Static methods are not dynamically overridden |
| Fields | Declared reference type | Fields are hidden, not polymorphically dispatched |

**Dig deeper:** covariant return types are allowed when overriding. Private methods are not overridden; final methods cannot be overridden. Why can `method(null)` be ambiguous for unrelated overload types?

## Composition vs. inheritance

### 5. Why does extending a collection to add a counter often fail?

A subclass may rely on undocumented calls between base-class methods. If both `addAll` and `add` increment a counter, internal delegation may double count. Compose a collaborator and define exactly what is counted instead.

```java
final class TrackingSink<T> {
    private final Collection<T> target;
    private long successfulAdds;
    TrackingSink(Collection<T> target) { this.target = target; }
    boolean add(T value) {
        boolean changed = target.add(value);
        if (changed) successfulAdds++;
        return changed;
    }
    long successfulAdds() { return successfulAdds; }
}
```

Ownership matters: this counts only adds through this wrapper. If other callers mutate `target`, it is not a total-history metric. It is also not thread-safe.

| Approach | Strength | Risk |
|---|---|---|
| Inheritance | Natural substitutable specialization; framework extension hooks | Fragile coupling to superclass implementation and lifecycle |
| Composition | Explicit delegation, easy replacement and testing | More forwarding; not automatically the same type as the delegate |

**Dig deeper:** state the “is-a” behavioral contract. Would a fixed-size list be a good subtype of a contract promising arbitrary insertions? How would you prevent callers bypassing your wrapper?

## SOLID under practical constraints

### 6. How do you recognize a SOLID violation in an actual service?

| Principle | Practical signal | Possible change | Cost to watch |
|---|---|---|---|
| Single responsibility | Tax rules and email templates force edits in the same class | Separate pricing, orchestration, and delivery | Splitting every method creates navigation overhead |
| Open/closed | Every new provider modifies a large conditional | Strategy registry behind a stable contract | Too many interfaces for stable simple logic |
| Liskov substitution | Subclass rejects valid base operations | Narrow contract or use composition | Shared syntax alone does not ensure shared semantics |
| Interface segregation | Client implements irrelevant methods that throw | Smaller capability interfaces | Excess fragmentation |
| Dependency inversion | Business rules construct vendor SDK clients directly | Depend on an owned port; adapt vendor API | Adapter maintenance and translation policy |

### 7. What is a concrete Liskov substitution failure?

If `Bird.fly()` promises all birds can fly, `Penguin.fly()` throwing unsupported-operation violates caller expectations. Separate the capability:

```java
interface Bird { void eat(); }
interface Flying { void fly(); }
final class Penguin implements Bird {
    public void eat() { /* ... */ }
}
final class Sparrow implements Bird, Flying {
    public void eat() { /* ... */ }
    public void fly() { /* ... */ }
}
```

**Dig deeper:** stronger preconditions, weaker postconditions, or broken invariants violate substitutability. A payment provider that silently ignores an idempotency key can violate a contract even if the code compiles. Test each implementation against a shared contract suite.

## Patterns with tradeoffs

### 8. Which pattern would you use, and what problem does it solve?

Start with a real variation or boundary: strategy for interchangeable behavior, an adapter for an external interface, a decorator for added behavior, and explicit state transitions for lifecycle rules. Avoid abstractions without an independent reason to vary.

Detailed pattern comparisons and the [Java adapter/decorator example](../System_Design/Design_Patterns.md#java-adapter-and-decorator-example) live in the [design-pattern guide](../System_Design/Design_Patterns.md).

### 9. When is an enum/state machine better than many boolean flags?

```java
enum OrderStatus { CREATED, PAID, SHIPPED, CANCELLED }
final class Order {
    private OrderStatus status = OrderStatus.CREATED;
    void markPaid() {
        if (status != OrderStatus.CREATED) {
            throw new IllegalStateException("payment transition not allowed");
        }
        status = OrderStatus.PAID;
    }
}
```

One state prevents combinations such as `paid=false, shipped=true` when those are invalid. An enum plus explicit transitions is often enough; use state objects when state-specific behavior becomes substantial.

**Dig deeper:** how does optimistic locking prevent two concurrent transitions? What happens when payment succeeded externally but the local transition failed? A state machine alone does not solve distributed consistency.

## Dependency injection and object lifecycle

### 10. Why constructor injection rather than constructing dependencies internally?

```java
final class ReminderService {
    private final Clock clock;
    private final ReceiptSender sender;
    ReminderService(Clock clock, ReceiptSender sender) {
        this.clock = Objects.requireNonNull(clock);
        this.sender = Objects.requireNonNull(sender);
    }
}
```

Constructor injection makes required dependencies explicit and enables deterministic tests using `Clock.fixed`. DI does not require Spring. Avoid constructors doing network I/O; separate construction from managed startup when necessary.

| Approach | Fit | Tradeoff |
|---|---|---|
| Constructor injection | Required collaborators | Large constructors can reveal too many responsibilities |
| Setter injection | Truly optional/reconfigurable dependency | Temporarily invalid states and concurrency during reconfiguration |
| Service locator | Narrow infrastructure lookup where justified | Hidden dependencies and runtime failures |

**Dig deeper:** who closes an injected HTTP client? Usually its owner, not every consumer. Why can singleton objects still be unsafe? How do scopes differ across tests, containers, JVMs, and replicas?

## Design exercise: checkout

### 11. Design checkout without a giant service or an unsafe distributed transaction

**Clarify:** can prices change? Can inventory expire? Is payment synchronous? What identifies a retry of the same request?

```java
interface InventoryPort {
    Reservation reserve(Cart cart, String operationId);
}
interface PaymentGateway {
    PaymentResult charge(Money amount, String idempotencyKey);
}
interface OrderRepository {
    Order load(OrderId id);
    void save(Order order); // actual persistence must detect concurrent updates
}
```

A checkout application service orchestrates ports; domain objects validate local transitions; adapters own DB/HTTP details. Record a durable operation ID, make repeated requests return the same outcome, and persist recoverable workflow state.

| Decision | Reasonable choice | Tradeoff |
|---|---|---|
| Remote call inside DB transaction | Sometimes required by a narrow workflow | Long-held locks/connections; remote success cannot be rolled back by SQL |
| State transitions plus compensation | Recover failures across systems | Intermediate states and reconciliation complexity |
| Domain event in memory | Lightweight local notification | Process crash can lose work |
| Transactional outbox | Save event and order in the same DB transaction | Publisher retries and consumer deduplication still needed |

**Dig deeper:** reservation succeeds and payment times out—do you know whether it charged? Query/reconcile by operation ID instead of blindly charging again. What if refund fails? Which states can operations staff inspect and repair?

## Refactoring and testing

### 12. How would you refactor a large conditional safely?

First characterize current behavior, including errors and edge cases. Extract cohesive branches behind a small contract, inject the selection rule, and migrate one path at a time. Do not rewrite unrelated persistence behavior during the extraction.

**Practical tests:** boundary-value tests for domain invariants; shared contract tests for interchangeable adapters; integration tests for persistence/concurrency; workflow tests for retries and partial failure. Mocking every method tends to couple tests to implementation order.

**Dig deeper:** inheritance vs. composition may be less important than stable contracts and ownership. How would you identify overengineering? Look for abstractions with no independent variation, ambiguous names, and simple changes requiring edits across many files.

## References

- [Java classes: inheritance, overriding, and constructors](https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html)
- [Java interfaces and default methods](https://docs.oracle.com/javase/specs/jls/se25/html/jls-9.html)
- [Java method invocation and overload resolution](https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.12)
- [Java Object equality contract](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/Object.html)
