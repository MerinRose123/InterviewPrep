# Memory Profiling and Performance Interview Cheat Sheet

[Study index](README.md) · Related: [Java memory](../Java_CheatSheet.md), [Python memory](../Python_CheatSheet.md), [observability](Observability_CheatSheet.md), [large-data jobs](Large_Data_Background_Processing_CheatSheet.md).

Commands are diagnostic examples, not actions run by this guide. Dumps/profiling have overhead and can contain credentials or user data; choose capture scope, access, and storage deliberately.

## Contents

- [1. What is a memory leak in a garbage-collected language?](#1-what-is-a-memory-leak-in-a-garbage-collected-language)
- [2. Heap vs. RSS vs. virtual memory vs. container memory?](#2-heap-vs-rss-vs-virtual-memory-vs-container-memory)
- [3. Walk through a leak investigation](#3-walk-through-a-leak-investigation)
- [4. How do you profile Python memory?](#4-how-do-you-profile-python-memory)
- [5. How do you profile Java memory and CPU?](#5-how-do-you-profile-java-memory-and-cpu)
- [6. What causes a Kubernetes OOMKilled event?](#6-what-causes-a-kubernetes-oomkilled-event)
- [7. CPU profiling vs. memory profiling vs. latency tracing?](#7-cpu-profiling-vs-memory-profiling-vs-latency-tracing)
- [8. How do you prevent leaks by design?](#8-how-do-you-prevent-leaks-by-design)
- [References](#references)

## 1. What is a memory leak in a garbage-collected language?

Unwanted data remains reachable, so the runtime cannot reclaim it. Common owners: unbounded dictionaries/caches, static collections, listeners, thread-local values, queued work, sessions, and closures. An unreachable object cycle is not necessarily a leak; runtime behavior and native resources matter.

**Scenario:** every export adds its DataFrame to a global dictionary but never removes it. The dictionary is the retention owner; calling GC does not make reachable data disappear.

| Symptom | Possible cause | Useful distinction |
|---|---|---|
| Live heap grows after comparable GC cycles | Retention leak or growing legitimate state | Inspect owner and business lifecycle |
| High allocation but stable live set | Temporary-object churn | Allocation rate vs. retained size |
| RSS grows while traced heap is stable | Native allocations, stacks, mappings, allocator retention | Process memory vs. runtime heap |
| Queue length and memory grow together | Arrival rate exceeds completion | Backpressure may be the fix |

**Dig deeper:** high memory is not proof of a leak. A bounded cache warming up can plateau normally. How do you distinguish legitimate growth from obsolete retained data?

## 2. Heap vs. RSS vs. virtual memory vs. container memory?

| Measurement | Meaning | Trap |
|---|---|---|
| Runtime heap | Managed object allocations | Excludes some native/runtime memory |
| RSS | Resident process pages | Includes more than managed live objects; shared pages complicate totals |
| Virtual address space | Address mappings/reservations | Not all is resident physical RAM |
| Container/cgroup usage | Charged usage under runtime/OS accounting | Can include non-heap categories and file cache |
| Peak memory | Maximum during an operation | Sampling may miss a short spike |

A process may release objects without RSS falling immediately because allocators retain arenas/pages. Do not repeatedly force GC as a substitute for understanding ownership and accounting.

**Dig deeper:** NumPy/Pandas/native buffers can escape some Python allocation visibility. Java direct buffers and metaspace consume memory outside the Java heap. Why can heap be below `-Xmx` when the container is OOM-killed?

## 3. Walk through a leak investigation

1. Capture workload, version, concurrency, data size, baseline memory, and growth timeline.
2. Compare repeated equal work after warmup; include idle/cleanup periods.
3. Correlate runtime live set, RSS, queues, threads, cache entries, and request/task rate.
4. Capture allocation profiles/snapshots and retention evidence at comparable points.
5. Find the retaining owner and why lifecycle cleanup failed.
6. Fix ownership/bounds/streaming; rerun sustained load and compare memory slope, peak, and latency.

**Dig deeper:** a restart mitigates but destroys evidence and does not prove a fix. A test that runs only one tiny request may never reveal a leak. What is your expected steady-state plateau and acceptable slope?

## 4. How do you profile Python memory?

```python
import tracemalloc
tracemalloc.start(10)
before = tracemalloc.take_snapshot()
# Run representative work here, including its intended cleanup.
after = tracemalloc.take_snapshot()
for stat in after.compare_to(before, "lineno")[:10]:
    print(stat)
current, peak = tracemalloc.get_traced_memory()
print({"traced_current": current, "traced_peak": peak})
tracemalloc.stop()
```

Start early enough to observe relevant allocations. Snapshot differences identify allocation sites, not automatically the reference retaining them. `tracemalloc` focuses on traced Python allocations; pair it with process/native memory evidence where necessary. [Python tracemalloc](https://docs.python.org/3/library/tracemalloc.html).

| Tool / approach | Use | Limitation |
|---|---|---|
| `tracemalloc` | Compare traced allocation snapshots | Not a complete native/RSS profiler |
| `cProfile` | Function CPU/call-time investigation | Overhead; not retained-memory ownership |
| Native-aware profiler such as Memray | Python/native allocation investigation | Environment/overhead/support constraints |
| OS process tools | RSS, mappings, threads | Do not identify domain ownership alone |

**Dig deeper:** `sys.getsizeof()` reports shallow size, not the whole object graph. Generators reduce materialization only if downstream code also streams rather than collecting everything.

## 5. How do you profile Java memory and CPU?

```sh
jcmd <pid> GC.heap_info
jcmd <pid> Thread.print
jcmd <pid> JFR.start name=incident settings=profile duration=60s filename=incident.jfr
# Potentially intrusive; plan safe capture conditions and disk capacity:
jcmd <pid> GC.heap_dump /safe/path/heap.hprof
# Requires Native Memory Tracking enabled when the JVM starts:
jcmd <pid> VM.native_memory summary
```

A histogram shows types/counts/shallow bytes; a heap-dump dominator tree and GC-root paths help identify retention owners. JFR can correlate allocations, CPU, GC, and blocking. Native Memory Tracking requires suitable startup configuration and does not cover every native-library allocation. [JDK diagnostic tools](https://docs.oracle.com/en/java/javase/21/troubleshoot/diagnostic-tools.html).

**Dig deeper:** a large class count can indicate class-loader retention; many threads consume native stacks. Why might increasing heap worsen total container pressure? Match tools and flags to the deployed JDK.

## 6. What causes a Kubernetes OOMKilled event?

A container can exceed its memory limit without Java/Python throwing a managed-language OOM first. Inspect termination reason, resource limits, node events, cgroup/process memory, heap/native allocation, concurrency, and workload peak.

```sh
kubectl describe pod <pod>
kubectl logs <pod> --previous
kubectl top pod <pod> --containers
# Metrics availability and retention vary; these do not reconstruct every past spike.
```

| Response | Appropriate when | Risk |
|---|---|---|
| Reduce concurrency/batch size | Peak work multiplies memory | Lower throughput |
| Stream/spill large intermediates | Whole-data materialization dominates | More I/O and cleanup |
| Bound caches/queues | Unbounded retained work | Need rejection/eviction policy |
| Increase limit/headroom | Valid working set is larger | Can hide a leak; scheduling/cost impact |
| Recycle worker | Temporary containment | Does not fix cause and may replay work |

**Dig deeper:** one 300 MB task × eight processes can exceed a 2 GB container before runtime overhead. Requests and limits solve different problems. A sampling dashboard may miss the actual peak.

## 7. CPU profiling vs. memory profiling vs. latency tracing?

CPU profiles show on-CPU execution hotspots; allocation profiles show allocation activity; retained-heap analysis shows reachable ownership; traces show request time across components, including waiting. Pick the tool from the symptom.

**Scenario:** p99 is high with low CPU and stable memory. Investigate DB locks, connection-pool wait, executor queueing, DNS/network, and external calls before optimizing a string loop. High CPU with heavy allocations may involve GC and allocation churn.

**Dig deeper:** profiling perturbs workloads; reproduce key findings with comparable traffic. Microbenchmarks need warmup and controls against dead-code elimination. Never average per-instance p99 values to claim a global p99.

## 8. How do you prevent leaks by design?

Give each resource a clear owner and lifetime. Bound cache entries/bytes, queued tasks, in-flight requests, batch size, and per-tenant work. Close files/streams/connections deterministically with context managers or try-with-resources. Remove listeners and clear thread/request context when ownership ends.

**Resume drill:** for the 16 GB export pipeline, describe per-worker memory, chunk size, number of workers, temporary storage, data sharing boundaries, and crash cleanup. State what you measured rather than inventing a memory reduction percentage.

## References

- [Python tracemalloc](https://docs.python.org/3/library/tracemalloc.html)
- [Python memory management](https://docs.python.org/3/c-api/memory.html)
- [JDK diagnostic tools](https://docs.oracle.com/en/java/javase/21/troubleshoot/diagnostic-tools.html)
- [Memray](https://bloomberg.github.io/memray/)
- [Kubernetes resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
