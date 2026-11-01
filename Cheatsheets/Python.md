# Senior Python Interview Questions: Concepts and Code

Interviewers often ask you to write code, then ask what happens when it fails or runs under load. The examples use modern Python 3. Some details apply only to CPython; those are labeled.

## Contents

- [Context managers](#1-context-managers)
- [Dataclasses](#2-dataclasses)
- [Instance, class, and static methods](#3-instance-class-and-static-methods)
- [Properties, getters, setters, and deleters](#4-properties-getters-setters-and-deleters)
- [Access modifiers and encapsulation](#access-modifiers-and-encapsulation-in-python)
- [Decorators](#5-decorators)
- [Generators, iterators, and coroutines](#6-generators-iterators-and-coroutines)
  - [Generators](#generator)
  - [Creating an iterator](#what-is-an-iterator-and-how-do-you-create-one)
  - [Coroutines and async code](#coroutines-and-async-code)
  - [Normal function vs coroutine](#what-is-a-coroutine-and-how-is-it-different-from-a-normal-function)
- [Futures](#7-futures)
- [Threads, processes, and asyncio](#8-threads-and-processes)
  - [When to use each concurrency option](#when-should-i-use-asyncio-threads-or-processes)
  - [Interview: concurrent API aggregator (pseudocode)](#interview-concurrent-api-aggregator-pseudocode)
- [Heap, stack, and Python memory](#9-heap-stack-and-python-memory)
- [Garbage collection and memory leaks](#10-garbage-collection-and-memory-leaks)
  - [Reference counting and garbage collection](#how-does-garbage-collection-work-in-cpython)
  - [Finding memory leaks](#how-do-you-diagnose-a-memory-leak)
- [Subprocesses](#11-subprocesses)
- [Circuit breaker](#12-circuit-breaker)
- [Metaclasses, `__new__`/`__init__`, and the diamond problem](#13-metaclasses-and-the-diamond-problem)
- [Dictionaries and collections](#14-dictionaries-and-collections)
  - [How dictionaries work internally](#how-does-a-dict-work-internally)
  - [Collection comparison](#how-do-lists-tuples-sets-dictionaries-and-deques-compare)
- [Argument passing, reference counting, copying, and identity](#15-argument-passing-reference-counting-copying-and-identity)
  - [Argument passing](#is-python-pass-by-value-or-pass-by-reference)
  - [Reference counting](#what-is-reference-counting-and-how-does-it-connect-to-garbage-collection)
  - [Shallow vs. deep copy](#what-is-the-difference-between-shallow-and-deep-copy)
  - [`==` vs. `is`](#what-is-the-difference-between--and-is)
- [Comprehensions and functional tools](#16-comprehensions-lambda-map-filter-and-reduce)
- [Exception handling and custom exceptions](#17-exception-handling-and-custom-exceptions)
- [Mocking in unit tests](#18-mocking-in-unit-tests)
- [HTTP requests with `requests`](#19-http-requests-with-requests)
- [Senior-level follow-up prompts](#20-senior-level-follow-up-prompts)
- [References](#references)

## 1. Context managers

### What is a context manager?

A context manager handles setup and cleanup for a block of code. The usual syntax is `with`:

```python
with open("input.txt", "r", encoding="utf-8") as file:
    contents = file.read()
```

When the block ends, Python closes the file, even if an error happens inside the block. This avoids forgetting to close it. The same pattern works for locks, database transactions, and temporary resources.

Behind the scenes, a context manager has `__enter__` and `__exit__` methods. `__enter__` runs at the start and returns the value after `as`. `__exit__` runs at the end. It can suppress an exception by returning `True`; most context managers let errors propagate.

For a small custom context manager, `contextlib.contextmanager` is often the simplest form:

```python
from contextlib import contextmanager

@contextmanager
def managed_file(path):
    file = open(path, encoding="utf-8")
    try:
        yield file
    finally:
        file.close()

with managed_file("input.txt") as file:
    contents = file.read()
```

The `finally` block runs when the `with` block ends, including when it raises an error. In real code, prefer the built-in `open()` context manager unless you need extra behavior. For async resources, use `async with` and an async context manager.

**Senior follow-ups:** What if setup partially succeeds and then fails? Can cleanup itself fail? Who owns the resource? If several resources are opened, are they all closed if a later open fails? Use `contextlib.ExitStack` when the number of resources is dynamic. Never rely on garbage collection to close an important resource.

## 2. Dataclasses

### What problem does `dataclass` solve?

It generates common data-container methods such as `__init__`, `__repr__`, and equality. It does not automatically validate input, make nested values immutable, or replace domain behavior.

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class UserId:
    value: int

@dataclass
class Job:
    name: str
    labels: list[str] = field(default_factory=list)

job = Job("reindex")
job.labels.append("urgent")
```

Use `default_factory` for mutable defaults; `labels=[]` would share one list across instances and is rejected by current dataclasses. `frozen=True` prevents assigning fields, but does not deeply freeze referenced objects. `slots=True` can reduce per-instance overhead in suitable versions, with trade-offs for dynamic attributes and inheritance.

**Equality/hash details:** by default, dataclasses compare fields. Frozen dataclasses can be hashable depending on options and field hashability. Do not make mutable value objects hashable if mutations can change equality or hash behavior. For keyword-only construction, consider `kw_only=True` where supported. Use explicit validation in `__post_init__` or a parsing layer for untrusted data.

## 3. Instance, class, and static methods

```python
class Temperature:
    scale = "C"

    def __init__(self, celsius: float):
        self.celsius = celsius

    def fahrenheit(self) -> float:             # instance method: gets self
        return self.celsius * 9 / 5 + 32

    @classmethod
    def from_fahrenheit(cls, value: float):    # gets cls; subclass-aware constructor
        return cls((value - 32) * 5 / 9)

    @staticmethod
    def is_valid(value: float) -> bool:        # gets no implicit self/cls
        return value >= -273.15

t = Temperature.from_fahrenheit(68)
assert round(t.celsius) == 20
assert t.fahrenheit() == 68
assert Temperature.is_valid(t.celsius)
```

- Use an instance method when behavior depends on instance state.
- Use a class method for behavior about the class, especially alternate constructors that should construct subclasses through `cls`.
- Use a static method for a related utility that needs neither instance nor class state. A module-level function may be clearer if it is not conceptually part of the class.

All three can be called through a class; instance methods need an explicit instance in that case. In Python these method decorators use descriptor binding behavior.

| Method | First argument | Best use |
|---|---|---|
| Instance method | `self` | Read or change one object's state |
| Class method | `cls` | Alternate constructors or behavior shared by the class |
| Static method | None added automatically | Utility related to the class but independent of its state |

## 4. Properties, getters, setters, and deleters

Python commonly exposes managed attributes with `property` instead of Java-style `get_x()` / `set_x()` methods. A property is a data descriptor: attribute access invokes its getter/setter/deleter methods.

```python
class Account:
    def __init__(self, balance: int):
        self.balance = balance  # routes through the setter

    @property
    def balance(self) -> int:  # getter
        return self._balance

    @balance.setter
    def balance(self, value: int) -> None:
        if value < 0:
            raise ValueError("balance cannot be negative")
        self._balance = value

    @balance.deleter
    def balance(self) -> None:
        del self._balance

a = Account(20)
a.balance = 30
del a.balance
```

Use a property when you need validation, derived values, or compatibility while changing internal storage. Keep property access unsurprising: network calls and expensive database reads should be explicit methods. The `@name.setter` and `@name.deleter` functions must use the same property name.

### How do custom descriptors implement a reusable property?

```python
class Positive:
    def __set_name__(self, owner, name):
        self.storage_name = "_" + name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance, self.storage_name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("must be positive")
        setattr(instance, self.storage_name, value)

    def __delete__(self, instance):
        delattr(instance, self.storage_name)

class Product:
    price = Positive()

p = Product()
p.price = 12
print(p.price)
del p.price
```

`__get__`, `__set__`, and `__delete__` form the descriptor protocol. Defining `__set__` or `__delete__` makes it a data descriptor, which takes precedence over an instance-dictionary entry. `__set_name__` receives the declared attribute name when the owner class is created.

## Access modifiers and encapsulation in Python

### How do you add public, protected, and private access modifiers in Python?

**Interview answer:** Python does not have Java-style `public`, `protected`, or `private` keywords. Access is communicated by naming conventions; two leading underscores also trigger **name mangling**, which reduces accidental attribute collisions but does not enforce security.

| Style | Example | Meaning | Enforced? |
|---|---|---|---|
| Public | `name` | Public API, freely accessible | No restriction |
| Non-public / “protected” convention | `_salary` | Internal implementation detail; subclasses can still use it | No |
| Name-mangled / “private” convention | `__password` | Rewritten to `_ClassName__password` in the class definition | Not true access control |
| Special (“dunder”) | `__init__` | Python-defined special method, **not** private | No |

```python
class Employee:
    def __init__(self):
        self.name = "Alice"          # public
        self._salary = 50_000        # internal-use convention
        self.__password = "secret"   # name-mangled

emp = Employee()
print(emp.name)                # Alice
print(emp._salary)             # 50000 (allowed)
# print(emp.__password)        # AttributeError
print(emp._Employee__password) # secret (still accessible)
```

### Is `__password` really private?

No. In a class definition, `__password` becomes `_Employee__password`. It primarily prevents accidental name collisions in inheritance. This is **not** a security boundary, and sensitive data should not be protected by naming conventions alone.

```python
class Parent:
    def __init__(self):
        self.__value = "parent"

    def read_parent(self):
        return self.__value

class Child(Parent):
    def __init__(self):
        super().__init__()
        self.__value = "child"

c = Child()
print(c.read_parent())  # parent
print(c._Child__value)  # child
# The two attributes do not overwrite one another.
```

### How do you implement a getter or setter?

Use `@property` to validate or compute an attribute while keeping normal attribute syntax:

```python
class Employee:
    def __init__(self, salary):
        self.salary = salary

    @property
    def salary(self):
        return self._salary

    @salary.setter
    def salary(self, value):
        if value < 0:
            raise ValueError("Salary cannot be negative")
        self._salary = value

emp = Employee(50_000)
emp.salary = 60_000
# emp.salary = -1  # ValueError
```

**Common interviewer traps:** A single underscore does not block external access; double underscores do not provide true privacy; `__init__` is a special method, not a private method; `@property` controls attribute behavior, not who can access it.

**30-second response:** “Python uses naming conventions instead of strict access-modifier keywords. Public names have no prefix, a single underscore signals an internal or protected-by-convention member, and two leading underscores trigger class-name mangling. None of these enforce Java-like private access. For controlled reads and writes, I use properties.”

## 5. Decorators

### What is a decorator?

A decorator is a callable that transforms or wraps a function/class. A `@decorator` line is roughly equivalent to rebinding the function name to `decorator(function)` when the definition executes.

```python
from functools import wraps
from time import perf_counter

def timed(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            print(f"{fn.__qualname__}: {perf_counter() - start:.4f}s")
    return wrapper

@timed
def calculate(n):
    return sum(range(n))
```

`wraps` preserves metadata such as the name and docstring and sets `__wrapped__`, helping documentation, debugging, and introspection. A decorator with options needs an outer factory:

```python
def retry(attempts):
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return fn(*args, **kwargs)
                except TemporaryError:
                    if attempt == attempts - 1:
                        raise
        return wrapper
    return decorate
```

| Decorator form | Syntax | Use when |
|---|---|---|
| No options | `@timed` | The decorator needs no configuration |
| With options | `@retry(3)` | The decorator needs settings |
| Async-aware | `async def wrapper(...): ...` | The wrapped function is a coroutine |

**Senior-level concerns:** define which exceptions are retried, include backoff/deadlines, preserve signatures/metadata, consider decorator order, and make sure sync decorators are not incorrectly applied to async functions. Caching or authorization decorators must use correct keys and must not create security bypasses. Decorators execute at import/definition time, so avoid expensive or stateful setup there.

## 6. Generators, iterators, and coroutines

### Generator

A generator function contains `yield`; calling it returns a lazy, stateful iterator. Each `next()` resumes at the suspended point. It can process large streams with bounded memory, but it is generally one-shot.

```python
def read_nonempty(lines):
    for line in lines:
        text = line.strip()
        if text:
            yield text

with open("input.txt", encoding="utf-8") as source:
    for row in read_nonempty(source):
        if should_stop(row):
            break
```

`yield from other_iterable` delegates iteration (and generator protocol details). A generator can receive values with `.send()` and exceptions with `.throw()`, but most application code uses generators as producers. A `return value` ends the generator; normal iteration sees `StopIteration`, not that return value.

### What is an iterator, and how do you create one?

An **iterable** is something you can loop over. Calling `iter(iterable)` gives you an **iterator**. An iterator remembers its current position and provides the next item each time `next()` is called. When there are no more items, it raises `StopIteration`.

```python
class CountDown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self  # this object is its own iterator

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value

for number in CountDown(3):
    print(number)  # 3, then 2, then 1
```

Most of the time, a generator function is the simpler way to make an iterator:

```python
def count_down(start):
    while start > 0:
        yield start
        start -= 1
```

The class version is useful when you need explicit iterator state or custom behavior. Iterators are usually one-shot; an iterable such as a list can create a fresh iterator for each loop.

### What is a coroutine, and how is it different from a normal function?

A **function** is a reusable block of code that performs a task. Calling a normal function executes its body immediately; the caller waits until it returns or raises an exception.

A **coroutine** can suspend execution and resume later while retaining its local state. In Python, calling a coroutine function defined with `async def` creates a coroutine object without executing its body. Awaiting it or scheduling it as a task lets it run.

| Detail | Normal function | Coroutine function |
|---|---|---|
| Definition | `def` (without `yield`) | `async def` (without `yield`) |
| Calling it | Executes the body and returns a result | Returns a coroutine object |
| Waiting | Blocking work blocks the calling thread | `await` can suspend execution so other tasks can run |
| Typical use | Synchronous logic | Concurrent I/O, such as API calls and database queries |

```python
import asyncio

def greet():
    return "Hello"

async def greet_async():
    await asyncio.sleep(0.1)  # simulates a non-blocking wait
    return "Hello asynchronously"

async def main():
    print(greet())                 # executes immediately
    coroutine = greet_async()     # body has not started yet
    print(await coroutine)        # executes and awaits the result

if __name__ == "__main__":
    asyncio.run(main())
```

**Interview answer:** “A normal function executes when called. Calling a coroutine function creates an object that must be awaited or scheduled. A coroutine can pause at `await`, allowing other tasks to run while it waits for I/O.”

An `await` does not always suspend: an already-ready awaitable may complete immediately. Coroutines do not automatically make CPU-heavy code faster, and blocking calls inside a coroutine still block the event-loop thread.

### Coroutines and async code

Calling an `async def` function creates a coroutine object. It does not execute to completion by itself. The event loop schedules it; `await` suspends it until the awaited operation can make progress.

```python
import asyncio

async def fetch_one(client, url):
    response = await client.get(url)  # client must have async I/O
    return response.status_code

async def main(client, urls):
    results = await asyncio.gather(
        *(fetch_one(client, url) for url in urls)
    )
    return results

# At a synchronous program entry point:
# results = asyncio.run(main(client, urls))
```

`asyncio.run()` owns and closes an event loop and normally belongs at the program boundary; do not call it inside an already-running event loop (for example many notebook/web contexts). `asyncio.gather` schedules awaitables concurrently, but does not make CPU-bound Python work parallel. Bound concurrency for large input sets rather than creating millions of tasks at once.

### Generator vs coroutine

A generator primarily produces values via iteration. A native coroutine is created by `async def` and participates in await scheduling. Historical generator-based coroutines existed, but modern application code should use `async def`. Both suspend and retain local state, but their protocols and scheduling roles differ.

| Concept | Created with | How it advances | Common use |
|---|---|---|---|
| Iterator | A class with `__iter__` and `__next__`, or a generator | `next()` / `for` | Produce a sequence of values |
| Generator | A function with `yield` | `next()` / `for` | Produce values lazily with little code |
| Coroutine | An `async def` function | Scheduled and resumed at `await` | Concurrent non-blocking I/O |

### Cancellation and structured task lifetime

Cancellation is delivered cooperatively at await points. Clean up in `finally` and re-raise `CancelledError` after cleanup unless there is a deliberate reason to suppress it. Own child tasks with `TaskGroup` on supported Python versions, or retain/await tasks explicitly. Avoid fire-and-forget tasks whose exceptions and lifetime are unobserved.

```python
async def use_resource(resource):
    try:
        return await resource.run()
    finally:
        await resource.close()
```

## 7. Futures

### What is a Future?

A Future is a placeholder for a result that may not be ready yet. It has pending, completed-with-result, or completed-with-exception states. Most asyncio code awaits tasks/coroutines and lets the event loop manage futures; callers should rarely construct an `asyncio.Future` directly. `concurrent.futures.Future` represents work submitted to a thread/process executor and is consumed using `.result()` or callbacks.

| Future type | Used with | Get the result |
|---|---|---|
| `concurrent.futures.Future` | Thread or process executor | `.result()` blocks the calling thread |
| `asyncio.Future` | Asyncio event loop | `await future` suspends the coroutine |

```python
from concurrent.futures import ThreadPoolExecutor

def blocking_lookup(key):
    return database_client.lookup(key)

with ThreadPoolExecutor(max_workers=8) as pool:
    future = pool.submit(blocking_lookup, "customer-42")
    result = future.result(timeout=2)  # blocks this thread; may raise timeout/error
```

Async version using an executor for a blocking function:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def lookup_async(pool, key):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(pool, blocking_lookup, key)
```

A timeout while waiting does not necessarily stop the underlying thread operation. Use a timeout supported by the client itself and ensure work has a cancellation/termination policy. Do not call blocking `.result()` on the event-loop thread for a future whose completion depends on that same loop.

## 8. Threads and processes

### Thread syntax and shared state

Threads share the process address space. Standard CPython's GIL limits simultaneous execution of Python bytecode, but threads can overlap blocking I/O. Shared mutable state still needs synchronization.

```python
from concurrent.futures import ThreadPoolExecutor

def fetch(url):
    return http_client.get(url, timeout=3)

with ThreadPoolExecutor(max_workers=16) as executor:
    responses = list(executor.map(fetch, urls))
```

Prefer a thread-safe queue, a lock around a real invariant, or immutable/message-passed state. Do not assume one statement or a group of statements is safe just because a particular CPython operation happens to be atomic today.

### Process syntax

Processes have separate address spaces and can execute Python CPU work on multiple cores, at the cost of startup, IPC, serialization, and memory.

```python
from concurrent.futures import ProcessPoolExecutor

def cpu_heavy(number):
    return sum(i * i for i in range(number))

if __name__ == "__main__":
    with ProcessPoolExecutor() as executor:
        values = list(executor.map(cpu_heavy, [1_000_000, 2_000_000]))
```

Worker functions and arguments generally need to be importable/picklable. The main guard is important for spawn-based process startup. Never assume a live database connection or lock can be safely shared with a child; create process-local resources in the worker.

| Property | Threads | Processes |
|---|---|---|
| Memory | Shared | Separate by default |
| Communication | Direct objects, but synchronize shared mutations | IPC/serialization or explicit shared memory |
| Python CPU parallelism in ordinary CPython | Generally limited by the GIL | Can run on multiple cores |
| Typical fit | I/O-bound blocking libraries | CPU-bound isolated jobs |
| Main costs | Races and lock contention | Startup, memory, serialization, lifecycle |

For either model: bound work, propagate errors, set deadlines, manage shutdown explicitly, and measure. Newer/free-threaded CPython configurations can change CPU parallelism assumptions; use facts about the deployed build.

### When should I use asyncio, threads, or processes?

| Option | Use it when | Avoid it when |
|---|---|---|
| `asyncio` | You have many concurrent I/O operations and your clients/libraries support `async` | Your code makes blocking calls or does long CPU work on the event loop |
| Threads | You use blocking I/O libraries or need to run several I/O tasks together | You expect pure Python CPU work to scale across cores in standard CPython |
| Processes | You have CPU-heavy work that can be split into independent jobs | Jobs are tiny, share lots of state, or spend more time serializing than working |

Pick the model that fits the workload and libraries already in use. For example, use `asyncio` for many concurrent async HTTP requests, threads for a blocking HTTP client, and processes for CPU-heavy image processing. In every case, limit the number of tasks/jobs in flight.

### Interview: concurrent API aggregator (pseudocode)

**Question:** aggregate user details, recent orders, and payment status from three external services. Start calls concurrently, give each a two-second timeout, tolerate payment failure, fail appropriately if the user service fails, limit downstream concurrency, and handle exceptions.

**Choice:** use `asyncio` with an async HTTP client because these calls spend most of their time waiting for network I/O. This is Python-like pseudocode, not a complete implementation.

**Assumptions:** user data is required. Payment is optional as specified; order-failure behavior was unspecified, so this example also returns partial data if orders fail. The two-second deadline includes waiting for a concurrency slot, so overload cannot cause an unlimited wait.

```text
// Created at application startup, shared across requests in this worker/event loop.
http = AsyncHTTPClient(connection_pool_limit=30)
downstream_slots = Semaphore(30)  // Example capacity; tune for downstream limits.

async function fetchService(service, user_id):
    try:
        async with timeout(2 seconds):  // Queue wait + complete HTTP operation.
            async with downstream_slots:
                response = await http.get(service.url, user_id=user_id)
                response.raiseForStatus()
                data = response.parseAndValidateJSON()
                return Success(data)
    catch Cancellation:
        raise  // Preserve client disconnect / endpoint cancellation.
    catch Timeout:
        return Failure("timeout")
    catch HTTPError, NetworkError, InvalidResponse:
        return Failure("upstream_failure")
    catch Exception as error:
        logInternalError(service.name, error)
        return Failure("internal_error")  // Do not expose exception details.

async function aggregate(user_id):
    tasks = [
        createTask(fetchService(UserService, user_id)),
        createTask(fetchService(OrderService, user_id)),
        createTask(fetchService(PaymentService, user_id))
    ]
    try:
        user, orders, payment = await gather(tasks)
        // All tasks were scheduled before awaiting; failures are result values.

        if user is Failure:
            if user.reason == "timeout":
                return 504, { error: "User service timed out" }
            if user.reason == "internal_error":
                return 500, { error: "Unable to aggregate user data" }
            return 502, { error: "User service unavailable" }

        return 200, {
            user: user.data,
            orders: orders.data if orders is Success else null,
            payment: payment.data if payment is Success else null,
            errors: failureReasonsFor(orders, payment)
        }
    finally:
        cancel any unfinished tasks
        await all tasks settling, collecting exceptions
```

The timeout must cancel the underlying async request and release the semaphore slot. Use an async HTTP client throughout; calling a blocking client inside a coroutine would block the event loop. Close the shared HTTP client at application shutdown.

| Situation | Expected behavior |
|---|---|
| All three calls succeed | Return combined data; latency is roughly the slowest call, rather than the sum |
| Payment fails or times out | Return user/orders with `payment: null` and an explicit error; do not imply payment failed financially |
| User times out | Return 504; other calls also have bounded lifetimes |
| User has a network/upstream HTTP failure | Return 502 under this example's contract |
| Orders fail | Return partial data under the stated assumption; confirm the interviewer's desired policy |
| Concurrency slots are full | Calls wait within their two-second budget, then time out if necessary |
| Endpoint is cancelled | Cancel and await unfinished tasks; propagate cancellation |

For a known user-service “user not found” response, map to 404 if the API contract defines that meaning. Avoid blindly forwarding every upstream status.

**Concurrency scope:** a semaphore created inside `aggregate()` would only limit that one request. The shared semaphore above limits one worker; multiple workers/replicas multiply the total. Enforce a fleet-wide limit through coordinated admission control or a gateway when required. A concurrency limit bounds in-flight calls, not requests per second. Bound inbound work/queues too under sustained overload.

#### Threading vs. multiprocessing vs. asyncio for this question

| Property | Threading | Multiprocessing | Asyncio |
|---|---|---|---|
| Execution | OS threads overlap blocking I/O | Separate processes can run on separate cores | Event loop switches tasks at awaits |
| Best fit | Blocking HTTP clients and other blocking I/O | CPU-heavy calculations | Many I/O calls with async libraries |
| Memory / overhead | Shared memory; thread stacks and scheduling | Separate memory; startup and serialization | Shared memory; lightweight tasks |
| CPU-bound Python on GIL-enabled CPython | Limited parallel bytecode execution | Parallel execution across cores | CPU work blocks the loop unless offloaded |
| Concurrency control | Shared bounded thread pool plus bounded submission | Bounded process pool plus bounded submission | Shared semaphore and connection pool |
| Timeout caveat | Timing out a future does not stop a running thread; configure HTTP deadlines | Timing out a future does not stop running process work | Cooperative cancellation; client must support it |
| Fit for this aggregator | Good if the HTTP library is blocking | Usually unnecessary overhead for network waits | Good if the HTTP library is async |

**What to say aloud:** “I would start all three calls together using asyncio, bound downstream requests with an application-level semaphore, and give each call a two-second deadline. Each call returns success or failure so payment failure does not discard the other results. User data is required, so its failure becomes an endpoint error. Threads are suitable for blocking I/O clients; processes are useful for CPU-heavy work.”

**Follow-up:** this version waits for all three bounded results before checking user failure. For fail-fast behavior, observe the user task first while the other tasks are already running; if it fails, cancel and await the remaining tasks.

## 9. Heap, stack, and Python memory

### Is a Python variable stored on the stack or heap?

Interview shorthand can mislead here. Python names are bindings to objects; CPython objects are generally allocated on the managed heap. A function call also has interpreter execution frames and native C stack activity, but you should not map Python variable lifetime directly to a C local variable. The language does not promise a simple “every local is on stack” memory layout.

The OS process has virtual memory regions (including stacks and heaps), while Python's allocator manages object memory inside the process. These are related but different layers. Avoid claiming that CPython uses one contiguous heap or that every Python object maps one-to-one to an OS allocation.

### What are heap and stack memory in general?

- A native **stack** supports call frames and typically has scoped lifetimes; each thread has a stack.
- A process **heap** is memory dynamically managed during execution.
- Python's object allocator obtains/manages memory for Python objects; implementation details include arenas/pools in CPython and can vary by version/build.

In Python interviews, explain object references and lifetimes, then clarify which layer (Python allocator, process virtual memory, or OS) the question means.

| Term | What it describes | Typical lifetime |
|---|---|---|
| Call stack | Function calls and local execution frames | Until a call returns |
| Python object heap | Objects such as lists, dicts, and class instances | While references keep them alive |
| Process memory | Memory the operating system gives the process | Until released by the process/runtime or process exit |

## 10. Garbage collection and memory leaks

### How does garbage collection work in CPython?

CPython primarily uses reference counting: each strong reference contributes to an object's count, and an object is usually reclaimed when no strong references remain. A cyclic collector detects unreachable reference cycles that reference counting cannot reclaim. Exact timing is not a language guarantee. `gc.collect()` can request a collection for diagnostics or specialized cases, but it is not a general fix for retained objects.

```python
import gc

gc.collect()  # returns number of unreachable objects found/collected
print(gc.get_stats())
```

Weak references (`weakref`) allow some relationships, such as observer/cache references, without keeping an object alive. `__del__` is not a reliable resource cleanup mechanism: cycles and interpreter shutdown complicate finalization. Use context managers for deterministic cleanup.

### What is a memory leak in Python?

Usually it means memory remains reachable or native memory is retained longer than intended, so process usage grows with workload. Python-managed memory may also be freed to an allocator but retained by the allocator for reuse, so RSS might not fall immediately. Distinguish a true growing live-object set from allocator retention, caches, fragmentation, and native extension allocations.

Common causes:

- Unbounded global lists, caches, registries, metrics labels, or queues.
- Tasks, callbacks, closures, or exception tracebacks retaining large object graphs.
- Reference cycles combined with finalizers or external references.
- Native libraries or extensions retaining memory outside `tracemalloc` visibility.
- A consumer slower than a producer, causing unbounded buffering.

### How do you diagnose a memory leak?

1. Reproduce a stable workload and measure RSS plus Python allocation trends over time.
2. Compare `tracemalloc` snapshots to find growing Python allocation sites.
3. Inspect object counts, references, caches, queues, task registries, and lifecycle paths.
4. Check native allocations separately when Python snapshots do not explain RSS.
5. Verify under the same workload that the suspected objects stop accumulating after a fix.

```python
import tracemalloc

tracemalloc.start()
before = tracemalloc.take_snapshot()
run_representative_workload()
after = tracemalloc.take_snapshot()
for stat in after.compare_to(before, "lineno")[:10]:
    print(stat)
```

Do not “fix” a leak by calling `gc.collect()` on every request. Find the reference or buffer that makes objects live, and bound caches/queues by size, time, or ownership scope.

## 11. Subprocesses

### How do you run an external command safely?

Use `subprocess.run` with an argument list, avoid `shell=True` for untrusted input, set a timeout, check the return code, and capture output only when its size is bounded.

```python
import subprocess

completed = subprocess.run(
    ["git", "status", "--short"],
    check=True,
    text=True,
    capture_output=True,
    timeout=5,
)
print(completed.stdout)
```

`check=True` raises `CalledProcessError` for a non-zero exit. `TimeoutExpired` signals deadline expiry; decide whether and how the child is terminated and cleaned up. Passing a string through a shell can create command injection if data is interpolated. Use `Popen` for streaming/long-running control, and ensure stdout/stderr are drained to avoid pipe deadlocks.

For async applications use `asyncio.create_subprocess_exec` and await `communicate()` or stream pipes; synchronous `subprocess.run()` blocks the event loop.

```python
import asyncio

async def command():
    proc = await asyncio.create_subprocess_exec(
        "python", "-c", "print('child')",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode())
    return stdout.decode()
```

## 12. Circuit breaker

Circuit Breaker is a resilience pattern, not a Python language feature. Its states, failure/recovery behavior, and the Python `pybreaker` example live in [Design Patterns](../System_Design/Design_Patterns.md#circuit-breaker).

## 13. Metaclasses and the diamond problem

**Priority:** constructors and method resolution are core; metaclass internals are optional depth unless the role requires framework internals.

### What is the difference between `__new__` and `__init__`?

`__new__` creates and returns the object. `__init__` sets up an object after it has been created. In ordinary classes, you usually write `__init__` only. `__new__` is mainly useful when controlling object creation, especially for immutable types or specialized class construction.

```python
class User:
    def __new__(cls, name):
        print("creating the object")
        return super().__new__(cls)

    def __init__(self, name):
        print("initializing the object")
        self.name = name

user = User("Asha")
```

`__init__` must return `None`; returning the new object is the job of `__new__`. If `__new__` returns an instance of the class, Python then calls `__init__` on it. If it returns something else, `__init__` is not called for that object.

| Method | Main job | Usually used for |
|---|---|---|
| `__new__(cls, ...)` | Create and return an object | Immutable types or custom object creation |
| `__init__(self, ...)` | Set up an object that already exists | Assigning instance attributes and validating inputs |

### What is a metaclass?

A metaclass is the class of a class; it controls class creation. `type` is the default metaclass. Metaclasses can inspect or transform the namespace as a class is created. Frameworks sometimes use them for model registration or declarative APIs, but `__init_subclass__`, class decorators, and descriptors are often simpler.

| Tool | Runs when | Good for |
|---|---|---|
| Class decorator | After the class is created | Wrapping or replacing one class |
| `__init_subclass__` | A subclass is created | Registering or checking subclasses |
| Metaclass | The class object is created | Changing class creation across a hierarchy |

```python
class RequireKind(type):
    def __new__(mcls, name, bases, namespace):
        if name != "Base" and "kind" not in namespace:
            raise TypeError(f"{name} must define kind")
        return super().__new__(mcls, name, bases, namespace)

class Base(metaclass=RequireKind):
    pass

class JsonHandler(Base):
    kind = "json"
```

In the metaclass `__new__`, `super().__new__` creates the class object. Multiple inheritance can cause a metaclass conflict when base classes use incompatible metaclasses; the metaclass of the child must be a compatible subclass of the base metaclasses. This complexity is one reason to avoid unnecessary metaclasses.

### What is the diamond problem?

The diamond occurs when two classes inherit from the same base and a child inherits from both. A naïve parent call can run shared base behavior twice or skip parts of the hierarchy. Python uses C3 MRO; cooperative `super()` follows that MRO so each class can participate once when all implementations cooperate.

```python
class Root:
    def __init__(self, **kwargs):
        print("Root")
        super().__init__(**kwargs)

class Left(Root):
    def __init__(self, **kwargs):
        print("Left")
        super().__init__(**kwargs)

class Right(Root):
    def __init__(self, **kwargs):
        print("Right")
        super().__init__(**kwargs)

class Child(Left, Right):
    def __init__(self, **kwargs):
        print("Child")
        super().__init__(**kwargs)

print(Child.__mro__)
Child()
# Child -> Left -> Right -> Root, then object
```

Use compatible cooperative signatures (often keyword arguments) and call `super()` once at each level. If a class calls `Root.__init__(self)` directly, it bypasses the MRO chain and can duplicate or skip initialization. `super()` means “next in this object's MRO,” not “my direct parent.”

## 14. Dictionaries and collections

### How does a `dict` work internally?

In CPython, a dictionary is implemented as a resizable hash table. Python calls `hash(key)` to find where the key should go, then uses equality (`==`) to check whether it found the right key. If two keys land in the same place, Python handles the collision and checks other entries. The exact table layout is an implementation detail.

```python
user_by_id = {42: "Asha", 77: "Mika"}
print(user_by_id[42])       # Asha
user_by_id[42] = "Asha R"  # update the value
```

Lookup, insertion, and deletion are usually **O(1)** on average. If many keys collide, they can take **O(n)**. Dictionaries resize as they grow to keep lookups efficient. In modern Python, dictionaries also preserve insertion order.

Keys must be hashable: their hash and equality behavior must stay stable while they are in the dictionary. Strings, numbers, and many tuples are valid keys; lists are not. A tuple is hashable only if all its elements are hashable.

```python
counts = {}
for word in ["tea", "coffee", "tea"]:
    counts[word] = counts.get(word, 0) + 1
```

**Interview detail:** equal keys must have equal hashes. A hash match alone does not prove keys are equal; Python also checks equality. Hash randomization and the table layout are implementation details, so do not depend on a particular slot or hash value.

### How do lists, tuples, sets, dictionaries, and deques compare?

| Type | Keeps order? | Allows duplicates? | Mutable? | Best for |
|---|---|---|---|---|
| `list` | Yes | Yes | Yes | An ordered collection that changes; indexing by position |
| `tuple` | Yes | Yes | No (shallowly) | A fixed ordered group of values; can be a dict key if its items are hashable |
| `set` | No guaranteed order | No | Yes | Unique values and fast membership checks |
| `dict` | Yes, insertion order | Keys are unique | Yes | Looking up a value by key |
| `collections.deque` | Yes | Yes | Yes | A queue where adding/removing at either end is efficient |

```python
from collections import deque

names = ["Asha", "Mika", "Asha"]
unique_names = set(names)
ages = {"Asha": 30, "Mika": 28}
queue = deque(["first", "second"])
queue.append("third")
next_item = queue.popleft()
```

List indexing is O(1); adding or removing near the front is O(n). Set and dict membership are O(1) on average (O(n) in the worst case). Deques are efficient at both ends; use a list for fast indexing in the middle. A tuple's immutability is shallow: it can still contain a mutable list.

## 15. Argument passing, reference counting, copying, and identity

### Is Python pass-by-value or pass-by-reference?

Python passes **object references by assignment**. A function parameter becomes a new local name for the same object. If that object is mutable, changes to it can be seen by the caller. Reassigning the local name does not reassign the caller's variable.

```python
def update(items):
    items.append("new")  # changes the shared list
    items = ["other"]    # only changes the local name

names = ["Asha"]
update(names)
print(names)  # ['Asha', 'new']
```

If a function should not mutate the caller's list, make a copy inside the function or document that it mutates the input. This is sometimes called **call-by-sharing**. It is not the same as copying the whole object for each call.

### What is reference counting, and how does it connect to garbage collection?

In CPython, an object keeps track of strong references to it. Assigning it to another name or putting it in a list adds a reference; deleting a name or removing it from a list removes one. When the count reaches zero, CPython can usually reclaim the object immediately.

| Mechanism | What it detects | What happens |
|---|---|---|
| Reference counting | How many strong references point to an object | CPython can reclaim it when the count reaches zero |
| Cyclic garbage collector | Unreachable groups that refer to one another | Finds cycles reference counting alone cannot reclaim |

```python
import sys

value = []
other_name = value
print(sys.getrefcount(value))  # includes a temporary reference for this call
del other_name                 # removes one reference
```

Do not rely on the exact number printed: `getrefcount()` itself adds a temporary reference, and interpreter versions and internal caches affect counts. It is a CPython debugging tool, not a way to manage memory.

Reference counting alone cannot reclaim a group of objects that refer to one another, even if nothing outside the group can reach them. CPython's cyclic garbage collector finds many such unreachable cycles:

```python
import gc

items = []
items.append(items)  # the list refers to itself
del items             # the cycle still refers to itself
gc.collect()           # asks the cyclic collector to run
```

The collector supplements reference counting; it does not fix objects that are still reachable through a global list, cache, task, or callback. Use `weakref` when a reference should not keep an object alive, and use context managers for files and other resources. Do not use `__del__` as the main cleanup mechanism.

### What is the difference between shallow and deep copy?

Assignment creates another name for the same object. A shallow copy creates a new outer container but shares objects inside it. A deep copy recursively copies nested objects too.

| Operation | New outer object? | Copies nested objects? |
|---|---:|---:|
| Assignment (`b = a`) | No | No |
| Shallow copy (`copy.copy(a)`) | Yes | No; nested references are shared |
| Deep copy (`copy.deepcopy(a)`) | Yes | Yes, recursively where supported |

```python
import copy

original = [[1, 2], [3, 4]]
alias = original                 # same outer list
shallow = copy.copy(original)    # new outer list; inner lists are shared
deep = copy.deepcopy(original)   # nested lists are copied too

original[0].append(99)
print(shallow)  # [[1, 2, 99], [3, 4]]
print(deep)     # [[1, 2], [3, 4]]
```

Use a shallow copy when sharing nested objects is intended. Use a deep copy only when you need independent nested data: it can be expensive, and copying everything can be wrong for locks, files, connections, or intentionally shared objects. For regular lists, `items.copy()` is also a shallow copy.

### What is the difference between `==` and `is`?

`==` compares values. `is` checks whether two names refer to the exact same object.

| Operator | Compares | Common use |
|---|---|---|
| `==` | Values, using the type's equality behavior | Compare contents or values |
| `is` | Object identity | Check singletons such as `None` |

```python
first = [1, 2]
second = [1, 2]

print(first == second)  # True: same contents
print(first is second)  # False: different list objects
```

Use `is None` to check for `None`. Do not use `is` to compare strings or numbers: Python may reuse some objects as an optimization, but that is not a value-comparison guarantee.

## 16. Comprehensions, lambda, map, filter, and reduce

### Comprehensions

A comprehension builds a list, set, or dictionary from an iterable. It is often the clearest way to express a simple transform or filter.

```python
squares = [number * number for number in range(5)]
evens = [number for number in range(10) if number % 2 == 0]
length_by_name = {name: len(name) for name in ["Asha", "Mika"]}
unique_lengths = {len(name) for name in ["Asha", "Mika", "Noah"]}
```

Use a generator expression `(expression for item in items)` instead of a list comprehension when you want values one at a time and do not need to store the whole result. Keep nested comprehensions short enough to read.

### `lambda`, `map`, and `filter`

`lambda` creates a small anonymous function with one expression. `map` applies a function to each item. `filter` keeps items for which a function returns true.

```python
double = lambda number: number * 2
print(double(4))

numbers = [1, 2, 3, 4]
doubled = list(map(lambda n: n * 2, numbers))
evens = list(filter(lambda n: n % 2 == 0, numbers))
```

In many cases, a comprehension is easier to read:

```python
doubled = [n * 2 for n in numbers]
evens = [n for n in numbers if n % 2 == 0]
```

One common lambda trap is late binding in a loop: closures look up the loop variable when called, so they can all use its final value. Bind the value when creating each function if needed: `functions = [lambda x=x: x for x in range(3)]`.

### `reduce`

`reduce` combines items into one result, applying a function repeatedly. It lives in `functools`:

```python
from functools import reduce

numbers = [1, 2, 3, 4]
product = reduce(lambda total, n: total * n, numbers, 1)
print(product)  # 24
```

The final `1` is the starting value. For totals, use the clearer built-in `sum(numbers)`. For most other operations, a loop or named function is easier to debug than `reduce`.

## 17. Exception handling and custom exceptions

### How do `try`, `except`, `else`, and `finally` work?

- `try`: code that may fail.
- `except`: handle a specific error.
- `else`: runs only if the `try` block had no error.
- `finally`: runs whether there was an error or not; use it for cleanup.

| Clause | When it runs | Typical purpose |
|---|---|---|
| `try` | First | Code that may raise an exception |
| `except` | If a matching exception is raised | Handle a known failure |
| `else` | If `try` succeeds | Handle the success path |
| `finally` | Either way | Cleanup that must always run |

```python
try:
    number = int(user_input)
except ValueError:
    print("Please enter a whole number")
else:
    print("You entered", number)
finally:
    print("Input processing finished")
```

Catch the narrowest error you can handle. Avoid bare `except:` because it also catches things like `KeyboardInterrupt` and can hide serious problems. Use a context manager instead of a `finally` block when managing a standard resource such as a file or lock.

### How do you define a custom exception?

Create a class derived from `Exception`. A custom exception gives callers a clear way to handle a particular failure.

```python
class PaymentDeclined(Exception):
    pass

def charge(card, amount):
    if not card.is_valid:
        raise PaymentDeclined("Card was declined")

try:
    charge(card, 50)
except PaymentDeclined as error:
    print("Payment failed:", error)
```

When translating a lower-level error into an application-level one, preserve the original cause with `raise ... from error`:

```python
try:
    save_to_database(record)
except DatabaseError as error:
    raise SaveFailed("Could not save record") from error
```

Inside an `except` block, bare `raise` re-raises the same exception with its traceback. `raise error` can change the traceback location. Avoid returning from `finally`, because it can hide a return value or exception from the earlier code.

## 18. Mocking in unit tests

### What is mocking?

Mocking means replacing a dependency with a controlled test object. It lets a unit test focus on your code without calling a real database, web service, or other slow or unreliable system.

| Tool | What it does | Example use |
|---|---|---|
| `Mock` | Creates a fake object whose behavior you set | Pass a fake service into a function |
| `patch` | Temporarily replaces a name in a module | Replace an imported API call during a test |

```python
from unittest.mock import Mock

def get_customer_name(customer_id, customer_service):
    customer = customer_service.get(customer_id)
    return customer.name

def test_get_customer_name():
    service = Mock()
    customer = Mock()
    customer.name = "Asha"
    service.get.return_value = customer

    result = get_customer_name(42, service)

    assert result == "Asha"
    service.get.assert_called_once_with(42)
```

For code that imports a dependency directly, `unittest.mock.patch` temporarily replaces the name used by that code:

```python
from unittest.mock import patch

def load_profile(user_id):
    return profile_api.fetch(user_id)

def test_load_profile():
    with patch("myapp.profile_api.fetch", return_value={"name": "Asha"}) as fetch:
        result = load_profile(42)

    assert result == {"name": "Asha"}
    fetch.assert_called_once_with(42)
```

Patch the name where the code under test looks it up, not necessarily where the dependency was originally defined. Mock behavior that matters to the test, such as a return value or failure; avoid asserting every internal call. Too many mocks can make tests pass even when real components do not work together, so keep integration tests for important boundaries.

## 19. HTTP requests with `requests`

`requests` is a popular third-party library for making synchronous HTTP calls. It is not part of Python's standard library.

```python
import requests

response = requests.get(
    "https://api.example.com/users",
    params={"active": "true"},
    timeout=(2, 5),  # connect timeout, read timeout
)
response.raise_for_status()
users = response.json()
```

Send JSON with `json=...`; Requests encodes it and sets the JSON content type:

```python
response = requests.post(
    "https://api.example.com/users",
    json={"name": "Asha"},
    timeout=5,
)
response.raise_for_status()
```

| Tool | What it does |
|---|---|
| `params=` | Adds URL query parameters |
| `json=` | Encodes a JSON request body |
| `raise_for_status()` | Raises an HTTP error for a 4xx/5xx response |
| `timeout=` | Limits how long to wait for connection/read activity |
| `requests.Session()` | Reuses connections and shares session settings/cookies |

Always set a timeout in production. A successful `response.json()` only means the response body was valid JSON; call `raise_for_status()` to check for an HTTP error. For repeated calls to one service, use a `Session`. Requests is synchronous; use an async HTTP client when calling from an asyncio event loop.

```python
with requests.Session() as session:
    response = session.get("https://api.example.com/profile", timeout=5)
    response.raise_for_status()
```

## 20. Senior-level follow-up prompts

For each topic, expect a question about correctness at scale:

1. How would you make a context manager safe if acquisition partially succeeds and then raises?
2. What breaks if a dataclass contains mutable state and is used as a dict key?
3. How would you test a decorator that wraps both sync and async functions?
4. How can a generator keep a file or database cursor alive longer than expected?
5. What happens to sibling tasks when one `asyncio.gather` input fails or is cancelled? How would you supervise task lifetime?
6. When can a `Future.result()` call deadlock, block a worker, or time out without stopping underlying work?
7. What work belongs in a thread, process, or event loop, and how will you cap in-flight work?
8. How would you tell Python heap growth from native memory growth or allocator retention?
9. What makes retry plus circuit breaker behavior amplify load instead of protecting a dependency?
10. How do timeout, output buffering, child termination, and untrusted arguments affect subprocess safety?
11. Why can `__del__` be unreliable, and what deterministic alternative would you use?
12. How does the MRO behave in the exact diamond hierarchy shown, and what if one class omits `super()`?

## References

- [Python data model: descriptors and attribute access](https://docs.python.org/3/reference/datamodel.html#implementing-descriptors)
- [Descriptor HOWTO](https://docs.python.org/3/howto/descriptor.html)
- [contextlib](https://docs.python.org/3/library/contextlib.html)
- [dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [threading](https://docs.python.org/3/library/threading.html) and [multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
- [garbage collector interface](https://docs.python.org/3/library/gc.html)
- [subprocess](https://docs.python.org/3/library/subprocess.html)
- [PyBreaker usage and configuration](https://github.com/danielfm/pybreaker)
- [Python FAQ: dictionary implementation](https://docs.python.org/3/faq/design.html#how-are-dictionaries-implemented-in-cpython)
- [`sys.getrefcount`](https://docs.python.org/3/library/sys.html#sys.getrefcount)
- [copy module](https://docs.python.org/3/library/copy.html)
- [Built-in functions: `map` and `filter`](https://docs.python.org/3/library/functions.html)
- [`functools.reduce`](https://docs.python.org/3/library/functools.html#functools.reduce)
- [Built-in exceptions](https://docs.python.org/3/library/exceptions.html)
- [`unittest.mock`](https://docs.python.org/3/library/unittest.mock.html)
- [Requests quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)
