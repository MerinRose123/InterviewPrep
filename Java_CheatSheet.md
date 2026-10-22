# Java Interview Cheat Sheet

Code-focused notes for senior software engineer interviews. Examples use modern Java; check the target JDK because some newer language features were previews before becoming final.

## Contents

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
