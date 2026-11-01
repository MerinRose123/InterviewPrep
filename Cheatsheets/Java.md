# Java Interview Cheat Sheet

Code-focused notes for senior software engineer interviews. Examples use modern Java; check the target JDK because some newer language features were previews before becoming final.

## Contents

- [JUnit lifecycle, assertions, and test doubles](#junit-lifecycle-assertions-and-test-doubles)

- [JVM, JRE, and JDK](#jvm-jre-and-jdk)
- [Java program entry point: `main`](#java-program-entry-point-main)
- [Major Java version features](#major-java-version-features)
- [Java Collections Framework](#java-collections-framework)
- [`Comparable` and `Comparator`](#comparable-and-comparator)
- [Generics](#generics)
- [Streams](#streams)
- [Concurrency and multithreading](#concurrency-and-multithreading)
- [`synchronized` vs. `volatile`](#synchronized-vs-volatile)
- [`Runnable`, `Callable`, and `Future`](#runnable-callable-and-future)
- [Virtual threads](#virtual-threads)
- [`throw` vs. `throws`](#throw-vs-throws)
- [Exception handling](#exception-handling)
- [Dependency injection](#dependency-injection)
- [`HashMap` internals and thread safety](#hashmap-internals-and-thread-safety)
- [`ConcurrentHashMap`](#concurrenthashmap)
- [Senior Java: practical interview questions](#senior-java-practical-interview-questions)
- [References](#references)

## JVM, JRE, and JDK

| Term | What it is | Main job |
|---|---|---|
| JVM (Java Virtual Machine) | Abstract machine implemented by a runtime | Loads/verifies bytecode and executes it; manages memory, garbage collection, and JIT compilation |
| JRE (Java Runtime Environment) | Runtime components needed to run Java programs: JVM plus core libraries and supporting files | Run compiled Java applications |
| JDK (Java Development Kit) | Runtime plus developer tools | Compile, package, debug, document, and run Java applications (`javac`, `jar`, `javadoc`, debugger, etc.) |

Simple relationship: **JDK = tools + runtime; runtime includes the JVM and Java libraries.** Historically, vendors commonly shipped a separate JRE installation. Since JDK 11, a separate JRE image is no longer bundled in the JDK in the old layout; vendors can still provide runtimes, and `jlink` can build a smaller custom runtime image.

## Java program entry point: `main`

The familiar Java application entry point is:

```java
public static void main(String[] args) {
    System.out.println("Hello");
}
```

| Part | Meaning |
|---|---|
| `public` | Launcher can access the method |
| `static` | JVM can call it without first creating an object |
| `void` | It does not return a value to the launcher |
| `main` | Conventional entry-point method name |
| `String[] args` | Command-line arguments |

**Is this exact signature still required?** For conventional class-based Java applications and broad compatibility, use it. Since Java 25, compact source files and instance `main` methods are also standard, so a small program can be written as:

```java
void main() {
    System.out.println("Hello");
}
```

The launcher can invoke a supported non-private instance `main` method in a compact source file. Frameworks and test runners may call application code through their own entry points, so a `main` method is not required in every Java class or library.

## Major Java version features

For interview prep, focus on the LTS releases below. Each row explains what the feature does and why it matters. Java has also had important non-LTS feature releases between these LTS versions; features can become final before the next LTS.

| LTS release | Headline features |
|---|---|
| Java 8 | Lambdas, functional interfaces, Streams, `Optional`, default interface methods, `java.time` |
| Java 11 | Standard HTTP Client, single-file source launch, Flight Recorder; long-term support release after Java 8 |
| Java 17 | Sealed classes; stronger encapsulation of JDK internals. Records, `instanceof` pattern matching, text blocks, and switch expressions were finalized in Java 16/15/14 respectively and are available by 17. |
| Java 21 | Virtual threads, record patterns, pattern matching for `switch`, sequenced collections |
| Java 25 | Scoped values, module import declarations, compact source files and instance `main` methods, flexible constructor bodies |

### Java 8

- **Lambdas and functional interfaces:** pass behavior as a small function, often to an API. A functional interface has one abstract method; `Predicate<T>` tests, `Function<T,R>` transforms, and `Consumer<T>` accepts a value.
- **Streams:** express collection processing as operations such as filter, transform, and collect. Pipelines are generally lazy until a terminal operation runs.
- **`Optional<T>`:** represent a value that may be absent in a return type, instead of returning `null` without a clear signal.
- **Default interface methods:** add a method implementation to an interface so existing implementors can inherit it.
- **`java.time`:** modern date/time types such as `LocalDate`, `Instant`, and `ZonedDateTime`; these are immutable and clearer than the older `Date`/`Calendar` APIs.

```java
import java.util.stream.Collectors;

List<String> names = users.stream()
    .filter(User::isActive)
    .map(User::name)
    .collect(Collectors.toList());
```

### Java 11

- **Standard HTTP Client:** `java.net.http.HttpClient` became a standard API. It supports synchronous `send()` and asynchronous `sendAsync()`, and HTTP/2.
- **Single-file source launch:** run a source file directly with `java Hello.java`, useful for small scripts and examples; normal applications are still compiled/packaged as usual.
- **Flight Recorder:** low-overhead diagnostics for investigating JVM performance and production behavior.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

class HttpClientExample {
    public static void main(String[] args) throws Exception {
        var client = HttpClient.newHttpClient();
        var request = HttpRequest.newBuilder(URI.create("https://example.com")).build();
        var response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println(response.statusCode());
    }
}
```

`var` for local variables was introduced in Java 10, not 11. It infers a local variable's static type at compile time; it does not make Java dynamically typed.

### Java 17

- **Sealed classes/interfaces:** explicitly limit which types can extend or implement a type. This makes a known set of variants easier to model and reason about.
- **Strong encapsulation:** internal JDK APIs are no longer broadly accessible by default. Applications should use supported public APIs instead of depending on JDK internals.
- **Useful features finalized just before 17:** records provide concise data-carrier classes; pattern matching for `instanceof` combines a type check and cast; text blocks simplify multiline strings; switch expressions return a value.

```java
sealed interface Result permits Success, Failure {}
record Success(String value) implements Result {}
record Failure(String message) implements Result {}

if (result instanceof Success success) {
    System.out.println(success.value()); // check and cast together
}
```

### Java 21

- **Virtual threads:** lightweight threads managed by the JVM. They let a service handle many concurrent tasks that wait on I/O using straightforward blocking code; they do not make CPU-heavy work faster by themselves.
- **Record patterns:** unpack a record's components during a type check.
- **Pattern matching for `switch`:** branch on types and values more clearly; the compiler can check that a sealed hierarchy is covered.
- **Sequenced collections:** common APIs such as `getFirst()`, `getLast()`, `addFirst()`, and `reversed()` make encounter order easier to work with.

```java
static String describe(Object value) {
    return switch (value) {
        case Integer i -> "int " + i;
        case String s -> "text " + s;
        case null -> "null";
        default -> "other";
    };
}
```

Record patterns unpack record components as part of the type match:

```java
record Point(int x, int y) {}
Object value = new Point(2, 3);

if (value instanceof Point(int x, int y)) {
    System.out.println(x + y);
}
```

Sequenced collections expose first/last elements and a reversed view:

```java
import java.util.ArrayList;
import java.util.List;
import java.util.SequencedCollection;

SequencedCollection<String> names = new ArrayList<>(List.of("Ada", "Grace"));
String first = names.getFirst();
SequencedCollection<String> backwards = names.reversed();
```

### Java 25

- **Scoped values:** safely share an immutable value down a call chain for a bounded scope; useful for request context and virtual-thread workloads, and an alternative to some `ThreadLocal` uses.
- **Module import declarations:** import all packages exported by a module with `import module ...;` rather than listing each package.
- **Compact source files and instance `main`:** reduce ceremony for small programs; a launchable program can omit an explicit class and use a supported instance `main`. The traditional `public static void main(String[] args)` remains the most portable form.
- **Flexible constructor bodies:** allow limited validation/computation before an explicit `super(...)` or `this(...)` constructor invocation, while still preventing access to the not-yet-initialized instance.

```java
import module java.base;

void main() {
    System.out.println(List.of("Java", "25"));
}
```

“Final” means a standard feature. Preview features require preview-enabled compile/run flags and may change between releases; do not treat a preview as a standard feature of that Java version.

Example Java 17 sealed hierarchy:

```java
public sealed interface Payment permits CardPayment, CashPayment {}

public final class CardPayment implements Payment {}
public non-sealed class CashPayment implements Payment {}
```

`sealed` restricts which classes may directly extend or implement the type. A permitted subtype must declare whether it is `final`, `sealed`, or `non-sealed`.

## Java Collections Framework

The Collections Framework provides interfaces and implementations for storing groups of objects. `Collection` is the common parent interface for lists, sets, and queues. **`Map` is part of the framework, but it does not extend `Collection`** because it stores key/value pairs rather than individual elements.

```text
Iterable
└── Collection
    ├── List      ordered; duplicates allowed
    ├── Set       unique elements
    └── Queue     elements held for processing
        └── Deque supports both ends

Map              key/value pairs (separate branch)
```

| Interface | Common implementation | Ordering / duplicate behavior | Typical use |
|---|---|---|---|
| `List` | `ArrayList` | Keeps position; allows duplicates | Indexed access and iteration; default general-purpose list |
| `List` / `Deque` | `LinkedList` | Keeps order; duplicates allowed | Queue/deque behavior; node overhead often makes it slower than `ArrayDeque` |
| `Set` | `HashSet` | No guaranteed iteration order; unique values | Fast membership checks |
| `Set` | `LinkedHashSet` | Insertion order; unique values | Set with predictable iteration order |
| `Set` | `TreeSet` | Sorted order; unique by comparator ordering | Ordered/range operations |
| `Queue` / `Deque` | `ArrayDeque` | Double-ended queue; no `null` values | Stack or queue without linked-node overhead |
| `Queue` | `PriorityQueue` | Head is highest/lowest priority; iteration is not fully sorted | Process next item by priority |
| `Map` | `HashMap` | No guaranteed iteration order; unique keys | General-purpose key/value lookup |
| `Map` | `LinkedHashMap` | Predictable insertion/access order | Ordered map or LRU-style building block |
| `Map` | `TreeMap` | Keys sorted | Ordered key/range queries |

| Operation | `ArrayList` | `HashSet` / `HashMap` | `TreeSet` / `TreeMap` |
|---|---:|---:|---:|
| Lookup by index/key | List index: O(1) | Average O(1) | O(log n) |
| Add/remove | End append is amortized O(1); middle insert/remove O(n) | Average O(1) | O(log n) |
| Keeps iteration order? | Yes, list order | No | Sorted order |

Use `ArrayList` by default for a list, `HashSet` for uniqueness/membership, `HashMap` for lookups, and `ArrayDeque` for stack/queue operations. Choose ordered or concurrent variants when their behavior is needed.

```java
import java.util.*;

List<String> names = new ArrayList<>();
Set<String> uniqueNames = new HashSet<>();
Map<String, Integer> scores = new HashMap<>();
Deque<String> stack = new ArrayDeque<>();
Queue<String> priorityQueue = new PriorityQueue<>();
```

`Collection` is an interface; `Collections` is a utility class with helpers such as sorting and unmodifiable wrappers. `List.of(...)`, `Set.of(...)`, and `Map.of(...)` create unmodifiable collections and reject `null` elements/keys/values.

## `Comparable` and `Comparator`

Both define ordering. `Comparable` is the type's natural/default order; `Comparator` is an external ordering that can be selected or composed for a particular task.

| | `Comparable<T>` | `Comparator<T>` |
|---|---|---|
| Method | `compareTo(other)` | `compare(left, right)` |
| Defined | Inside the class being ordered | Separately, often as a lambda |
| Use | One natural order | Multiple or custom orders |
| Example | Sort employees by their ID by default | Sort by salary, then by name |

`compare(a, b)` returns a negative number if `a` comes first, zero if equal for ordering, and a positive number if `a` comes after `b`. Avoid subtraction for numeric comparisons because it can overflow.

```java
import java.util.Comparator;
import java.util.List;

record Employee(String name, String department, int salary) {}

List<Employee> employees = ...;

employees.sort(Comparator.comparingInt(Employee::salary)
                         .thenComparing(Employee::name));

employees.sort(Comparator.comparingInt(Employee::salary).reversed());

// Null handling can be made explicit
Comparator<String> names = Comparator.nullsFirst(Comparator.naturalOrder());
```

For consistent behavior, ordering should generally agree with `equals` when values are used in sorted sets/maps. If `compare(a, b) == 0` for unequal objects, a `TreeSet` may treat them as duplicates.

## Generics

Generics let classes and methods work with a type while preserving compile-time checks. They reduce casts and catch type errors before runtime.

```java
class Box<T> {
    private T value;
    void set(T value) { this.value = value; }
    T get() { return value; }
}

Box<String> box = new Box<>();
box.set("hello");
String text = box.get();
```

### Bounds and wildcards

```java
import java.util.List;

static <T extends Comparable<T>> T max(T a, T b) {
    return a.compareTo(b) >= 0 ? a : b;
}

static double total(List<? extends Number> values) { // producer: read Numbers
    return values.stream().mapToDouble(Number::doubleValue).sum();
}

static void addDefaults(List<? super Integer> values) { // consumer: write Integers
    values.add(0);
}
```

| Syntax | Meaning | Usual use |
|---|---|---|
| `<T extends Number>` | Type parameter must be `Number` or a subtype | Generic method/class needing number operations |
| `? extends T` | Unknown subtype of `T`; safe to read as `T` | Producer of `T` values |
| `? super T` | Unknown supertype of `T`; safe to add `T` values | Consumer of `T` values |
| `<?>` | Some unknown type | Read values as `Object`; cannot safely add non-null values |

**PECS:** Producer Extends, Consumer Super. Java generics are invariant: `List<Integer>` is not a subtype of `List<Number>`. Generic type arguments are mostly erased at runtime, so `new T()` and `instanceof List<String>` are not allowed in the general case.

## Streams

A Stream is a pipeline for processing data from a source (such as a collection). It describes operations; it is not itself a collection and does not store the elements. Intermediate operations are usually lazy and run when a terminal operation asks for a result.

```java
List<String> names = employees.stream()
    .filter(e -> e.salary() >= 100_000)       // intermediate
    .map(Employee::name)                     // intermediate
    .sorted()                                // intermediate
    .toList();                               // terminal: runs the pipeline
```

| Operation type | Examples | What it does |
|---|---|---|
| Intermediate | `filter`, `map`, `flatMap`, `sorted`, `distinct`, `limit` | Returns another stream; normally lazy |
| Terminal | `toList`, `collect`, `forEach`, `count`, `reduce`, `findFirst` | Produces a result or side effect; consumes the stream |

`map` transforms one element to one result; `flatMap` transforms one element to a stream and flattens the streams. A stream should generally be consumed once. Prefer side-effect-free operations; avoid mutating shared state inside `map` or parallel streams.

```java
Map<String, Long> countByDepartment = employees.stream()
    .collect(java.util.stream.Collectors.groupingBy(
        Employee::department, java.util.stream.Collectors.counting()));
```

Parallel streams use a shared fork-join pool and are not automatically faster. They can hurt when work is small, blocking, order-sensitive, or mutates shared state; measure first.

## Concurrency and multithreading

Concurrency means multiple tasks make progress during overlapping time. Parallelism means tasks execute at the same instant on different cores. Java threads can be scheduled concurrently; whether they run in parallel depends on the runtime and hardware.

| Problem | Common Java tool |
|---|---|
| Protect a critical section | `synchronized`, `Lock` |
| Publish a simple state flag | `volatile` (visibility/order, not compound atomicity) |
| Atomic counter/update | `AtomicInteger`, `AtomicReference`, or `LongAdder` for highly contended stats |
| Run/manange task lifecycles | `ExecutorService` |
| Share concurrent key/value state | `ConcurrentHashMap` |

```java
class Counter {
    private int value;

    public synchronized void increment() { value++; }
    public synchronized int get() { return value; }
}
```

`volatile int count; count++` is still unsafe for concurrent increments: increment is a read-modify-write sequence, not one atomic action. Use synchronization or an atomic type. Establish clear ownership for mutable data and prefer immutable values where practical.

## `synchronized` vs. `volatile`

Both are used in concurrent programs, but they solve different problems. `synchronized` uses a monitor lock to make a critical section mutually exclusive and to make changes visible when threads acquire/release the same lock. `volatile` makes reads/writes of one variable visible across threads and orders those accesses, but it does not lock or make a multi-step operation atomic.

| | `synchronized` | `volatile` |
|---|---|---|
| Mutual exclusion | Yes, for code using the same monitor | No |
| Visibility | Yes, through monitor unlock/acquire | Yes, for reads/writes to the volatile field |
| Makes `count++` atomic? | Yes, if all increments use the same lock | No |
| Good fit | Protect related mutable state/invariants | Independent state flag or one value safely published |

```java
class SafeCounter {
    private int count;

    public synchronized void increment() { count++; }
    public synchronized int get() { return count; }
}
```

```java
class Worker {
    private volatile boolean stopped;

    void stop() { stopped = true; }
    void run() {
        while (!stopped) {
            doOneUnitOfWork();
        }
    }
}
```

Use `AtomicInteger` or a lock for counters. Use `volatile` when a thread writes a simple state and other threads only read/write that state independently; it is not a substitute for protecting a multi-field invariant.

### Thread lifecycle and executors

Creating a `Thread` directly is useful for learning, but real services usually submit tasks to an executor so thread creation and shutdown are managed consistently.

```java
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

try (ExecutorService pool = Executors.newFixedThreadPool(4)) {
    pool.submit(() -> System.out.println("work"));
} // orderly shutdown and wait for submitted work
```

Use bounded concurrency for platform-thread pools. Choose pool size based on workload and resources; too many threads can increase memory use, context switching, and downstream contention.

## `Runnable`, `Callable`, and `Future`

`Runnable` represents work with no return value and no checked exception in its method signature. `Callable<V>` returns a value and may throw a checked exception. Submitting either to an `ExecutorService` can return a `Future` to observe completion, get the result, or cancel.

| | `Runnable` | `Callable<V>` |
|---|---|---|
| Method | `void run()` | `V call() throws Exception` |
| Returns result | No | Yes |
| Checked exception in signature | No | Yes |
| Typical submit result | `Future<?>` | `Future<V>` |

```java
import java.util.concurrent.*;

ExecutorService pool = Executors.newFixedThreadPool(2);
try {
    Future<Integer> future = pool.submit(() -> 20 + 22); // Callable<Integer>
    Integer answer = future.get();                       // waits; may throw
    System.out.println(answer);
} finally {
    pool.shutdown();
}
```

`Future.get()` blocks until completion. `CompletableFuture` adds composition such as `thenApply`, `thenCompose`, and `exceptionally`, allowing asynchronous pipelines.

## Virtual threads

Virtual threads are lightweight threads managed by the Java runtime. They make a thread-per-request style practical for applications with many concurrent tasks that spend time waiting on blocking I/O (database, network, files).

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> response = executor.submit(() -> fetchFromService());
    System.out.println(response.get());
}
```

| Virtual threads help with | They do not |
|---|---|
| Many concurrent blocking I/O tasks | Make CPU-bound code run faster by themselves |
| Simpler code than callback-heavy async flows | Remove database/API connection limits |
| Creating a lightweight thread per task | Replace backpressure, timeouts, or resource limits |

Do not pool virtual threads just to limit their number; use semaphores or other resource-specific limits for scarce services. Keep blocking operations interruptible where possible and set timeouts. Use CPU-sized platform-thread pools for CPU-bound tasks.

## Exception handling

An exception represents an abnormal condition that interrupts normal control flow. Java exceptions are objects in the `Throwable` hierarchy:

| Type | Checked by compiler? | Typical meaning | Usual handling |
|---|---|---|---|
| Checked exception (`IOException`, for example) | Yes: catch it or declare it | Recoverable condition outside the method's control | Handle or declare with `throws` |
| Unchecked exception (`RuntimeException` and subclasses) | No | Programming error or invalid call/state | Fix the cause; catch only when a layer can respond meaningfully |
| `Error` | No | Serious JVM/environment problem | Usually do not catch in application code |

```java
try {
    return Files.readString(path);
} catch (NoSuchFileException e) {
    return ""; // recover only because missing file is expected here
} catch (IOException e) {
    throw new UncheckedIOException("Could not read configuration", e); // preserve cause
}
```

Prefer specific catches, and catch at the layer that can recover, translate, or add useful context. Avoid empty catches and avoid catching `Exception` broadly unless the boundary must log/translate failures.

Use try-with-resources for `AutoCloseable` resources; Java closes them even if the block throws. If both the body and `close()` fail, the close failure is recorded as a suppressed exception.

```java
try (var reader = Files.newBufferedReader(path)) {
    return reader.readLine();
}
```

Custom exceptions make domain failures clear to callers:

```java
class InsufficientFundsException extends Exception {
    InsufficientFundsException(String message) { super(message); }
}

void withdraw(long amount) throws InsufficientFundsException {
    if (amount > balance) {
        throw new InsufficientFundsException("Not enough funds");
    }
    balance -= amount;
}
```

## `throw` vs. `throws`

`throw` throws an exception object at a point in the code. `throws` declares in a method signature that the method may let an exception escape to its caller.

```java
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

static String readFirstLine(Path path) throws IOException {
    if (path == null) {
        throw new IllegalArgumentException("path is required");
    }
    try (var reader = Files.newBufferedReader(path)) {
        return reader.readLine();
    }
}
```

| Keyword | Where used | Meaning |
|---|---|---|
| `throw` | Method body | Actually raise one exception instance |
| `throws` | Method/constructor declaration | Declare possible checked exceptions for callers |

Checked exceptions must be caught or declared. Unchecked exceptions (`RuntimeException` and subclasses) do not need to be declared. Catch exceptions at a layer that can recover, add useful context, or translate them; avoid swallowing them.

## Dependency injection

Dependency injection (DI) means an object receives the collaborators it needs instead of constructing them internally. This reduces coupling and makes tests easier because dependencies can be replaced with fakes or mocks.

```java
interface PaymentGateway {
    void charge(String customerId, long cents);
}

class CheckoutService {
    private final PaymentGateway gateway;

    // Constructor injection: dependency is explicit and required
    CheckoutService(PaymentGateway gateway) {
        this.gateway = gateway;
    }

    void checkout(String customerId, long cents) {
        gateway.charge(customerId, cents);
    }
}
```

| Injection style | Notes |
|---|---|
| Constructor injection | Preferred for required dependencies; supports immutability and easy unit testing |
| Setter injection | Useful for optional/reconfigurable dependencies; object can be incomplete before setter call |
| Field injection | Convenient in some frameworks but hides dependencies and makes plain unit tests harder |

Frameworks such as Spring build and wire objects (beans) from configuration. DI is a design pattern; Spring is one framework that provides a container for it.

## `HashMap` internals and thread safety

`HashMap<K,V>` stores entries in a bucket array. It hashes the key, maps the hash to a bucket, then compares keys with `equals()` within that bucket. A collision occurs when different keys map to the same bucket. In modern OpenJDK implementations, heavily collided buckets can become balanced trees once implementation thresholds are met; resizing occurs as the map grows past its capacity/load-factor threshold.

In the standard implementation, the hash is spread before selecting a bucket; for a power-of-two table, the bucket is selected using the low bits of the hash. The default load factor is `0.75`, so the table resizes when its threshold (capacity × load factor) is crossed. These are implementation details; do not rely on a particular bucket layout in application code.

Common OpenJDK interview detail: the default initial capacity is 16 and the default load factor is 0.75. A collision bucket can be treeified at roughly eight entries when the table is large enough (capacity at least 64); otherwise the map may resize first. Treat these thresholds as implementation details that can vary by JDK.

| Operation | Typical average cost | Worst case / note |
|---|---:|---|
| `get` / `put` | O(1) | Collisions can worsen lookup; tree bins improve heavily collided buckets |
| Iteration | O(capacity + size) | Excessively large initial capacity can slow iteration |
| Resize | O(n) work during growth | Amortized cost is usually efficient across many inserts |

`HashMap` is **not thread-safe**. Concurrent updates can lose data or expose inconsistent behavior; fail-fast iterators are bug detection, not thread safety. Use external synchronization for a map protected by one lock or use `ConcurrentHashMap` for concurrent access.

```java
Map<String, Integer> counts = new HashMap<>();
counts.merge("blue", 1, Integer::sum); // concise single-threaded counting
```

Keys should have stable `equals()` and `hashCode()` behavior while stored. Equal keys must have equal hash codes. Mutating fields used by `hashCode()` after insertion can make a key effectively unreachable.

## `ConcurrentHashMap`

`ConcurrentHashMap` is designed for concurrent access. Reads generally do not block; updates coordinate at a finer granularity than locking the entire map. The exact internal algorithm depends on the Java implementation/version; avoid describing it as a fixed segment-lock design (that was used in older JDKs).

| Feature | `HashMap` | `ConcurrentHashMap` |
|---|---|---|
| Thread-safe for concurrent access | No | Yes for its individual operations |
| `null` key/value | Allows one null key and null values | Does not allow null keys or values |
| Atomic compound helpers | No | Methods such as `putIfAbsent`, `compute`, and `merge` provide atomic per-key operations |
| Iterator behavior | Fail-fast on structural modification (best effort) | Weakly consistent; can reflect some concurrent updates without throwing `ConcurrentModificationException` |
| Whole-map transaction/snapshot | No | No; separate operations are not one atomic transaction |

```java
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

var counts = new ConcurrentHashMap<String, LongAdder>();
counts.computeIfAbsent("blue", key -> new LongAdder()).increment();
```

Use `compute`, `merge`, or `putIfAbsent` instead of a racy `if (map.get(key) == null) map.put(...)` sequence. Keep mapping functions short and avoid recursively modifying the same map from them.

## Senior Java: practical interview questions

Related sheets: [OOP design questions](OOP.md) and [Spring Boot questions](SpringBoot.md). OOP pillars, inheritance, polymorphism, SOLID, and design patterns live in the OOP sheet.

**How to answer:** explain the mechanism, show the smallest useful example, name a failure mode, compare alternatives, and describe how you would verify the choice. Snippets are focused fragments; imports and application collaborators may be omitted. Baseline is Java 17 unless marked otherwise.

### 1. Why can a key become unreachable in a HashMap?

**Scenario:** a customer is inserted as a key, its email changes, and lookup starts returning `null`. If equality/hash fields change, lookup can select a different bucket. Use immutable identity fields. Equal objects must have equal hash codes; the reverse is not required. `equals` must be reflexive, symmetric, transitive, consistent, and false for `null`.

```java
record CustomerKey(long tenantId, long customerId) {}
Map<CustomerKey, String> names = new HashMap<>();
names.put(new CustomerKey(7, 42), "Ada");
System.out.println(names.get(new CustomerKey(7, 42))); // Ada
```

`==` compares reference identity for objects; `equals` expresses logical equality. Records generate component-based equality, but array components still use array identity unless you override behavior.

**Dig deeper:** why override both methods? What if every key returns hash code 1? How does `TreeMap` define duplicate keys? How would database-generated IDs affect entity equality before/after persistence?

### 2. Is Java pass-by-reference? Why does reassignment not affect the caller?

Java always passes values. For an object argument, the copied value is a reference: mutation can be visible through that reference, but replacing the local reference does not replace the caller's variable.

```java
static void change(List<String> items) {
    items.add("visible");
    items = new ArrayList<>(); // only changes this local variable
}
```

**Dig deeper:** explain why a `swap(Object a, Object b)` method cannot swap caller variables. A `final` reference prevents reassignment, not mutation of the referenced object.

### 3. Why is String immutable, and when does concatenation become expensive?

Immutability permits safe sharing, stable hash keys, and pooling. Literals are interned; `new String("x")` creates a distinct object. Do not use `==` for content. Repeated concatenation in a loop can repeatedly copy growing content; use a builder.

```java
String a = "java";
String b = new String("java");
System.out.println(a == b);      // false
System.out.println(a.equals(b)); // true
StringBuilder out = new StringBuilder();
for (String part : parts) out.append(part);
String result = out.toString();
```

| Choice | Practical fit | Cost / trap |
|---|---|---|
| `String` | Values, keys, a few concatenations | Loop accumulation can create many intermediate values |
| `StringBuilder` | Locally building text | Mutable; unsafe for concurrent mutation |
| `StringBuffer` | Legacy APIs requiring synchronized methods | Individual method synchronization does not make a multi-call workflow atomic |
| `intern()` | Deliberately canonicalizing a controlled vocabulary | Retention and lookup overhead; measure before interning arbitrary inputs |

**Dig deeper:** why is `s += x` different inside a large loop? Why are `StringBuilder` instances usually local? Why avoid logging credentials even when stored in a mutable array?

### 4. How do you create an immutable value? Is a record deeply immutable?

Make state private, prevent subclass mutation, validate at construction, and defensively copy mutable inputs and outputs. Records make component references final; referenced objects can still change.

```java
record OrderSnapshot(long id, List<String> tags) {
    OrderSnapshot {
        tags = List.copyOf(tags); // detached, unmodifiable list; rejects null elements
    }
}
```

This is sufficient for immutable `String` elements; mutable elements need their own copying/ownership policy.

| Technique | Benefit | Limitation |
|---|---|---|
| Unmodifiable wrapper | Cheap view | Original collection can still change |
| `List.copyOf` | Snapshot of element references | Shallow copy |
| Deep copy / immutable element model | Prevents nested state changes | Allocation and model complexity |

**Dig deeper:** can a record be a mutable map key? Does `final` make an object thread-safe? What is the difference between ownership and synchronization?

### 5. What language traps appear in production code?

| Question | Practical answer / syntax | Failure mode |
|---|---|---|
| `final` vs. `finally` vs. `finalize`? | `final` restricts reassignment/extension/overriding; `finally` performs cleanup; `finalize()` is deprecated for removal | Finalization is unpredictable; use try-with-resources |
| Can boxing throw? | `Integer x = null; int y = x;` throws NPE | Nullable DB fields unexpectedly unboxed |
| Can wrapper identity be trusted? | `Integer.valueOf(1000).equals(1000)` checks value | `==` results depend on object identity/caching |
| Is `static` per object? | Belongs to the class identity, including its defining class loader | Shared mutable state and class-loader retention |
| Why `BigDecimal` for money? | `new BigDecimal("0.10")`; specify scale and rounding policy | Binary floating point cannot exactly represent many decimal fractions |

`new BigDecimal("1.0").equals(new BigDecimal("1.00"))` is false because scale matters; `compareTo` returns zero. Decide whether scale belongs in your domain equality before using these as keys.

**Dig deeper:** why should `finally` avoid `return`? It can hide the original return value or exception. Why is monetary currency as important as amount?

### 6. What lives on the stack, heap, and in metaspace?

Threads have JVM stacks with invocation frames and local variables; objects/arrays are conceptually on the heap. A local reference and its object are different things. HotSpot metaspace holds class metadata in native memory. JIT optimizations can eliminate allocations, so avoid claiming every source-level allocation necessarily materializes on the heap.

| Symptom | Likely direction | Evidence to collect |
|---|---|---|
| `StackOverflowError` | Recursion / excessive call depth | Stack trace and recursive cycle |
| `OutOfMemoryError: Java heap space` | Live set too large or leak | Heap dump, dominator tree, paths to GC roots |
| Metaspace OOM | Excess classes / retained class loaders | Class-loading metrics and loader retention |
| Unable to create native thread | Thread count / OS or memory limits | Thread count, stack sizes, container limits |
| Process killed without Java OOM | Container/native-memory pressure | Container events and process RSS |

**Dig deeper:** increasing heap can hide a leak and leave less native headroom. How would you distinguish an allocation spike from retained growth after GC?

### 7. How does GC work, and how would you investigate a memory leak?

GC finds objects reachable from roots such as live thread references and static fields of reachable classes; unreachable cycles can be collected. A Java leak means unwanted objects remain reachable, often through caches, listeners, queues, static collections, or thread-local state.

**Investigation:** compare post-GC live-set trends under comparable load; inspect allocation and GC telemetry; take an authorized heap dump; inspect dominators and retention paths; reproduce the ownership bug and validate retained size after the fix. Dumps may contain application data and can pause a process.

```sh
jcmd <pid> GC.heap_info
jcmd <pid> Thread.print
jcmd <pid> JFR.start name=incident settings=profile duration=60s filename=incident.jfr
# Intrusive: plan disk space and operational impact before requesting a heap dump.
jcmd <pid> GC.heap_dump /safe/path/heap.hprof
```

| Approach | Fits | Tradeoff |
|---|---|---|
| G1 | General-purpose balance of throughput and pauses | Pause goals are targets; tuning needs workload evidence |
| ZGC | Workloads prioritizing low pauses | Concurrent work and memory headroom costs |
| Parallel GC | Throughput-oriented batch jobs | Potentially longer stop-the-world pauses |

Collector availability/defaults depend on JDK and vendor. Measure allocation rate, pause distribution, throughput, and CPU before switching. `System.gc()` is a request, not a leak fix.

**Dig deeper:** why can low heap use coexist with high RSS? What does a cache need besides thread safety? Distinguish weak/soft references from explicit size and expiry policies.

### 8. How do class loading and initialization cause surprises?

A class is loaded, linked (verification, preparation, resolution), then initialized when required by active use. Static initialization is coordinated by the JVM. Class identity includes the defining class loader, so identical class names loaded independently can be incompatible.

```java
class ClientHolder {
    private ClientHolder() {}
    private static class Lazy {
        static final Client INSTANCE = new Client();
    }
    static Client instance() { return Lazy.INSTANCE; }
}
```

The holder idiom uses class initialization for safe lazy publication. It does not make `Client` internals thread-safe. Avoid slow network calls and circular dependencies in static initializers.

**Dig deeper:** `ClassNotFoundException` vs. `NoClassDefFoundError`? Explicit loading can fail to find a class; linkage can fail because a class/dependency is unavailable or prior initialization failed. What retains a class loader after redeployment?

### 9. What does happens-before mean? How do you safely publish state?

Happens-before provides visibility and ordering guarantees; it does not mean tasks must run simultaneously or make compound operations atomic. Relevant edges include unlock to subsequent lock of the same monitor, volatile write to subsequent read, and thread start/join relationships.

```java
final class ConfigStore {
    private volatile Map<String, String> current = Map.of();
    void reload(Map<String, String> next) {
        current = Map.copyOf(next); // publish a complete immutable snapshot
    }
    String get(String key) { return current.get(key); }
}
```

A reader sees a published snapshot. Two separate `get` calls may observe different snapshots; capture one reference when a consistent multi-key read matters. Do not let `this` escape during construction.

**Dig deeper:** why is double-checked locking broken without `volatile`? Why does adding `sleep` fail to establish safe publication? See the [Java memory model](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html).

### 10. When would you choose a lock, CAS, or LongAdder?

| Choice | Best fit | Tradeoff |
|---|---|---|
| `synchronized` | Small critical section / related state | Blocking; monitor entry has no timed/interruptible acquisition API |
| `ReentrantLock` | Timed/interruptible locking, multiple conditions | Must unlock in `finally`; fairness can cost throughput |
| `AtomicInteger` / CAS | Single-variable state transitions | Retry contention; multi-field invariants still require design |
| `LongAdder` | Highly contended statistics | `sum()` is not an atomic snapshot during updates; unsuitable for quota enforcement |
| Immutable snapshots | Read-heavy configuration | Copying cost; coordinated writes still needed |

```java
private final ReentrantLock lock = new ReentrantLock();
boolean reserve() throws InterruptedException {
    if (!lock.tryLock(100, TimeUnit.MILLISECONDS)) return false;
    try {
        if (available == 0) return false;
        available--;
        return true;
    } finally {
        lock.unlock();
    }
}
```

**Dig deeper:** explain CAS retry loops and the ABA problem. Never perform irreversible external effects inside a retryable update function. What happens if two balances must change atomically?

### 11. How do deadlock, starvation, and livelock differ?

Deadlock: tasks wait cyclically for resources. Starvation: a task repeatedly fails to get execution/resources. Livelock: tasks keep reacting/retrying without useful progress.

**Scenario:** transfers lock source then destination; opposite transfers deadlock. Acquire locks in a stable global order, with an explicit tie policy, or use a single coordinating lock. Timeouts bound waiting but do not by themselves guarantee correctness.

```java
// Account IDs are unique; every code path must use this same lock ordering.
Account first = a.id() < b.id() ? a : b;
Account second = a.id() < b.id() ? b : a;
synchronized (first) {
    synchronized (second) {
        // validate and update both balances under these locks
    }
}
```

**Dig deeper:** collect multiple thread dumps; look for owner/waiter cycles. Database deadlocks require DB diagnostics too. How would you keep network I/O out of the critical section?

### 12. How should threads wait, communicate, and stop?

| API | Behavior | Practical caution |
|---|---|---|
| `Thread.sleep` | Delays current thread; retains held monitors | Timing is not synchronization |
| `Object.wait` | Releases that object's monitor while waiting; reacquires before return | Hold monitor; test condition in a loop for spurious wakeups |
| `BlockingQueue` | Coordinates producers/consumers | Bound capacity to prevent unlimited buffering |
| `CountDownLatch` | One-shot completion gate | Cannot reset |
| `Semaphore` | Limits concurrent resource users | Release only after successful acquisition |
| Interruption | Cooperative stop signal | Propagate `InterruptedException` or restore status when translating |

```java
try {
    Task task = queue.take();
    process(task);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
    return; // terminate this worker loop / task
}
```

**Dig deeper:** `Thread.interrupted()` clears the current thread's status; `isInterrupted()` does not. `notify` does not release the lock immediately. Why are higher-level queues safer than hand-written wait/notify protocols?

### 13. How do you size an executor and handle overload?

CPU-heavy tasks generally start with concurrency near available CPU capacity; blocking workloads need measurement of wait time and resource limits. Queue size is part of the latency and memory budget. `newFixedThreadPool` bounds workers but uses an unbounded queue.

```java
ThreadPoolExecutor pool = new ThreadPoolExecutor(
    8, 8, 0, TimeUnit.MILLISECONDS,
    new ArrayBlockingQueue<>(200),
    new ThreadPoolExecutor.AbortPolicy());
try {
    pool.execute(task);
} catch (RejectedExecutionException e) {
    // reject at the boundary with a deliberate retry/backpressure policy
}
// At application shutdown: pool.shutdown(); await termination within a deadline.
```

| Overload policy | Benefit | Risk |
|---|---|---|
| Abort / explicit rejection | Fast, visible overload | Caller must translate and handle failure |
| Caller-runs | Slows submitting thread | Can stall request/event-loop threads; after shutdown it discards tasks |
| Unbounded queue | Absorbs short bursts | Latency and memory can grow without bound |
| Drop policy | Useful for explicitly disposable work | Silent data loss if applied to business operations |

**Dig deeper:** monitor queue wait, active workers, rejection count, and downstream saturation. Why can a task waiting for another task in the same saturated pool deadlock? See [executor configuration rules](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html).

### 14. How do you compose CompletableFuture safely?

Use `thenApply` for synchronous transformation, `thenCompose` for a dependent asynchronous operation, and `thenCombine` for independent results. Choose an executor deliberately for blocking work.

```java
CompletableFuture<User> user = CompletableFuture.supplyAsync(
    () -> loadUser(id), ioExecutor);
CompletableFuture<Profile> profile = user
    .thenCompose(u -> loadProfileAsync(u.id()))
    .orTimeout(800, TimeUnit.MILLISECONDS);
CompletableFuture<Profile> observed = profile.whenComplete((value, error) -> {
    if (error != null) logFailure(error); // observation; do not throw here
});
```

| Method | Purpose | Trap |
|---|---|---|
| `exceptionally` | Recover with a value | A fake success can conceal failure |
| `handle` | Transform success or failure | Must deliberately handle both branches |
| `whenComplete` | Observe outcome | A throwing callback can affect dependent completion |
| `get` | Wait with checked failures / optional timeout | Blocks caller |
| `join` | Wait with unchecked completion failure | Also blocks; not inherently asynchronous |

Timeout completion does not automatically stop the underlying network/DB call. Configure transport timeouts and cancellation separately. See [CompletableFuture policies](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html).

**Dig deeper:** what executor runs a non-async continuation? What happens to request context across threads? Why does `allOf` not return a list of results?

### 15. When do virtual threads help, and what remains bounded?

They fit high-concurrency blocking I/O, while CPU capacity and DB/HTTP connection capacity remain finite. Use a semaphore or connection pool for scarce downstream resources. A large number of virtual threads can still retain a large amount of request state.

```java
// Java 21+; use a shared limiter for this downstream across requests.
Semaphore permits = new Semaphore(50);
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    Future<String> f = executor.submit(() -> {
        if (!permits.tryAcquire(100, TimeUnit.MILLISECONDS)) {
            throw new RejectedExecutionException("downstream busy");
        }
        try { return blockingCallWithTimeout(); }
        finally { permits.release(); }
    });
    System.out.println(f.get());
}
```

**Dig deeper:** where do you bound queued/waiting requests? What is the effect of thread-local data per virtual thread? On JDK 21, blocking inside `synchronized` can pin a carrier; JDK 24's JEP 491 removes monitor-related pinning, but native/foreign-code cases still require attention. Diagnose against the deployed JDK, rather than applying old blanket rules.

### 16. What stream and Optional pitfalls matter in real code?

```java
Map<String, Long> totals = orders.stream().collect(
    Collectors.groupingBy(Order::status, Collectors.counting()));
Map<Long, Order> byId = orders.stream().collect(
    Collectors.toMap(Order::id, Function.identity(), (oldValue, newValue) -> newValue));
String display = userOptional.map(User::name).orElseGet(this::loadDefaultName);
```

| Choice | Use | Tradeoff |
|---|---|---|
| Loop | Stateful logic, early exits, complex error paths | More explicit bookkeeping |
| Sequential stream | Clear transformation / aggregation | Debugging complex pipelines can be harder |
| Parallel stream | Measured independent CPU work with enough data | Shared resources, ordering, and splitting overhead |
| `orElse(value)` | Cheap fallback already available | Argument evaluates eagerly |
| `orElseGet(supplier)` | Expensive fallback | Supplier runs only when empty |

`toMap` without a merge rule throws for duplicate keys. `Stream.toList()` is unmodifiable; `Collectors.toList()` does not promise a concrete type or mutability. Use `toCollection(ArrayList::new)` when a mutable `ArrayList` is required. Captured local variables must be final/effectively final, but captured objects can still be mutable.

**Dig deeper:** why can `peek(...).count()` skip expected side effects? Optimizations can eliminate unnecessary traversal. Why must a parallel reduction be associative? Why is a shared `ArrayList` inside `parallelStream().forEach` unsafe?

### 17. How would you diagnose a slow Java endpoint?

**Work through:** reproduce workload → inspect p50/p95/p99 and errors → split queueing, CPU, GC, DB, and network time → use traces and profiles → change one bottleneck → compare under the same load. High latency with low CPU often points to waiting; high CPU requires a CPU profile rather than guessing.

| Evidence | Useful question |
|---|---|
| JFR / profiler | Where is CPU or allocation concentrated? |
| Thread dumps | Are workers blocked, waiting, or stuck in downstream calls? |
| GC logs / live-set trend | Are pauses or allocation pressure responsible? |
| Connection-pool metrics | Are requests waiting for DB connections? |
| JMH microbenchmark | Is a local algorithm faster after warmup and dead-code controls? |

**Dig deeper:** why is a single `System.nanoTime()` loop misleading? JIT warmup, dead-code elimination, GC, and workload bias. How does a larger pool worsen an already overloaded database?

### 18. Practical coding follow-ups

| Exercise | What to implement | Follow-up to defend |
|---|---|---|
| Frequency counter | `merge` sequentially; concurrent map plus atomics for shared updates | Null policy, contention, consistency of snapshots |
| Top-K events | Bounded priority queue, O(n log k) | Tie policy, stream size, approximate alternatives |
| LRU cache | Access-order `LinkedHashMap` with eviction | Access mutates order; thread safety, TTL, stampede prevention |
| Producer/consumer | Bounded `BlockingQueue` and interruptible workers | Shutdown, poison-pill count, failure/retry ownership |
| Deduplicate events | Stable key plus atomic insertion | Process-local state fails across replicas/restarts; durable uniqueness needed |

For each exercise, explain input constraints, complexity, edge cases, concurrency assumptions, and how failures affect correctness.

## JUnit lifecycle, assertions, and test doubles

### What is JUnit, and what runs a test?

JUnit Platform supports test discovery/execution; Jupiter supplies the programming and extension model used below. Vintage supports older JUnit tests where configured. These examples use Jupiter APIs shared by common JUnit 5/6 setups; select dependencies compatible with your project/JDK. JUnit 4 uses different lifecycle annotations, such as `@Before` rather than `@BeforeEach`.

### What is the test lifecycle?

| Annotation / setting | Meaning | Interview trap |
|---|---|---|
| `@BeforeAll` | Setup once before the class's tests | Normally static with the default per-method instance lifecycle |
| `@BeforeEach` | Setup before each test invocation | A parameterized test runs this for each invocation |
| `@Test` | A test method | Do not depend on another test running first |
| `@AfterEach` | Cleanup after each invocation | Release resources even when assertions fail |
| `@AfterAll` | Class-level cleanup | Normally static with the default lifecycle |
| `@TestInstance(PER_METHOD)` | New test-class instance for each method; default | Static/external resources can still leak state |
| `@TestInstance(PER_CLASS)` | Reuse one instance; permits non-static class lifecycle methods | Mutable instance state can couple tests, especially with parallel execution |

Conceptual order: before-all → [before-each → test → after-each] for each invocation → after-all. Test method order is not a substitute for isolation. Extensions provide setup/teardown and injection; for example Mockito's Jupiter extension initializes annotated mocks.

### Which assertion should I use?

| Assertion | Checks |
|---|---|
| `assertEquals(expected, actual)` | Value equality; use a delta where appropriate for floating-point comparisons |
| `assertSame(expected, actual)` | Object identity, not equivalent values |
| `assertTrue` / `assertFalse` | A boolean condition; include useful failure context |
| `assertNull` / `assertNotNull` | Presence or absence |
| `assertArrayEquals` / `assertIterableEquals` | Array / iterable contents and order |
| `assertThrows(Type.class, action)` | Expected exception type or subtype; returns the exception for further checks |
| `assertThrowsExactly(Type.class, action)` | Exact exception class |
| `assertAll(...)` | Group independent assertions and report multiple failures |
| `assertTimeout(...)` | Check elapsed time while executing in the calling thread; not an automatic hard cancellation boundary |

JUnit assertions are not Java's optional `assert` statement. Test externally meaningful results and exceptions; avoid asserting incidental implementation details or brittle full exception messages.

```java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.*;

class BookingRulesTest {
    private BookingRules rules;

    @BeforeEach
    void setUp() {
        rules = new BookingRules();
    }

    @Test
    void acceptsPositiveQuantity() {
        assertEquals(3, rules.validate(3));
    }

    @ParameterizedTest
    @ValueSource(ints = {0, -1, -100})
    void rejectsNonPositiveQuantity(int quantity) {
        var failure = assertThrows(IllegalArgumentException.class,
                () -> rules.validate(quantity));
        assertEquals("quantity must be positive", failure.getMessage());
    }

    static class BookingRules {
        int validate(int quantity) {
            if (quantity <= 0) {
                throw new IllegalArgumentException("quantity must be positive");
            }
            return quantity;
        }
    }
}
```

The exact message assertion above is appropriate only if that message is intentionally part of the contract. Parameterized tests require Jupiter parameter support. `@CsvSource` suits input/expected pairs; `@MethodSource` supplies richer objects or cases.

### Dummy, stub, fake, mock, and spy?

A **test double** replaces a collaborator for a test; its purpose matters more than its library class name.

| Double | Purpose | Example |
|---|---|---|
| Dummy | Fills a required parameter but is unused in the test | An unused callback |
| Stub | Supplies controlled answers | Fixed exchange rate or simulated timeout |
| Fake | Working simplified implementation | In-memory repository; does not prove real database locking behavior |
| Mock | Supports verification of expected interactions | Verify that a notification is sent once |
| Spy | Records/delegates behavior of an object, often calling real methods | Partial test around a real collaborator; can trigger real side effects |

Mockito example; `Notifier` is a nested test interface, so no application types are needed:

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class NotificationTest {
    interface Notifier {
        boolean available();
        void send(String message);
    }

    static class BookingService {
        private final Notifier notifier;
        BookingService(Notifier notifier) { this.notifier = notifier; }
        boolean confirm() {
            if (!notifier.available()) return false;
            notifier.send("Booked");
            return true;
        }
    }

    @Test
    void sendsWhenAvailable() {
        Notifier notifier = mock(Notifier.class);
        when(notifier.available()).thenReturn(true); // Stubbing

        BookingService service = new BookingService(notifier);
        boolean sent = service.confirm();

        assertTrue(sent);                           // State/outcome assertion
        verify(notifier).send("Booked");            // Interaction verification
    }
}
```

The service is real; only its notification collaborator is replaced. `verify(mock)` checks once by default; use `never()` when absence is the contract. Use argument captors for meaningful outgoing data, not every intermediate call. On a spy, `when(spy.method())` can execute the real method during setup; `doReturn(value).when(spy).method()` can avoid that call. Mockito is separate from JUnit.

### What should remain an integration test?

A mock cannot prove SQL correctness, transaction advice, tenant isolation, HTTP serialization, or a cloud provider's behavior. Unit-test decisions using controlled collaborators, then test important boundaries with the real framework/database or a suitable integration environment. Do not replace the object under test with a mock and claim its behavior was verified.

**Follow-ups:** Why does sharing a fixture make tests order-dependent? What does `assertThrows` actually execute? Why can a fake repository miss a race? How do you prevent a spy from making a real network call? Why is passing a direct unit test insufficient for `@Transactional`? See [Spring testing boundaries](SpringBoot.md#testing-and-production-diagnosis).

Sources: [JUnit user guide](https://docs.junit.org/current/user-guide/), [instance lifecycle](https://docs.junit.org/current/writing-tests/test-instance-lifecycle.html), [assertions](https://docs.junit.org/current/writing-tests/assertions.html), [Mockito API](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html).

## References

- [Java release notes](https://www.oracle.com/java/technologies/javase/jdk-relnotes-index.html)
- [OpenJDK JEP index](https://openjdk.org/jeps/0)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
- [JEP 321: HTTP Client](https://openjdk.org/jeps/321)
- [JEP 328: Flight Recorder](https://openjdk.org/jeps/328)
- [JEP 330: Launch Single-File Source-Code Programs](https://openjdk.org/jeps/330)
- [JEP 409: Sealed Classes](https://openjdk.org/jeps/409)
- [JEP 431: Sequenced Collections](https://openjdk.org/jeps/431)
- [JEP 440: Record Patterns](https://openjdk.org/jeps/440)
- [JEP 441: Pattern Matching for `switch`](https://openjdk.org/jeps/441)
- [JEP 506: Scoped Values](https://openjdk.org/jeps/506)
- [JEP 511: Module Import Declarations](https://openjdk.org/jeps/511)
- [JEP 512: Compact Source Files and Instance Main Methods](https://openjdk.org/jeps/512)
- [JEP 513: Flexible Constructor Bodies](https://openjdk.org/jeps/513)
- [Java `Comparator` API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/Comparator.html)
- [Java Streams package documentation](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/package-summary.html)
- [Java `HashMap` API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/HashMap.html)
- [Java `ConcurrentHashMap` API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html)
- [Java `ExecutorService` API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ExecutorService.html)
- [Java concurrency tutorial](https://docs.oracle.com/javase/tutorial/essential/concurrency/)
- [Java Language Specification: Threads and Locks](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)
- [Java exception-handling tutorial](https://docs.oracle.com/javase/tutorial/essential/exceptions/)
- [Java generics tutorial](https://docs.oracle.com/javase/tutorial/java/generics/)
- [Java Collections Framework documentation](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/doc-files/coll-index.html)
- [JEP 512: Compact Source Files and Instance Main Methods](https://openjdk.org/jeps/512)
- [JDK/JRE image changes in later Java releases](https://docs.oracle.com/en/java/javase/26/migrate/migrating-from-jdk-8-later-jdk-releases.html)
- [Spring dependency injection](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)

- [Java ThreadPoolExecutor API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)
- [Java CompletableFuture API](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CompletableFuture.html)
- [JEP 491: Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491)
