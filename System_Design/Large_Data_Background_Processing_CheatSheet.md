# Large Data and Background Processing Interview Cheat Sheet

[Study index](README.md) · Related: [messaging](Messaging_Kafka_CheatSheet.md), [memory profiling](Memory_Profiling_Performance_CheatSheet.md), [workflows](Workflow_Orchestration_CheatSheet.md).

Examples use Celery 5.x/Python conventions. Broker, worker pool, acknowledgement, and result-backend behavior depend on configuration; test the exact failure mode you depend on.

## Contents

- [1. How would you process a 16 GB CSV without running out of memory?](#1-how-would-you-process-a-16-gb-csv-without-running-out-of-memory)
- [2. Design an asynchronous export pipeline](#2-design-an-asynchronous-export-pipeline)
- [3. Celery broker vs. worker vs. result backend?](#3-celery-broker-vs-worker-vs-result-backend)
- [4. Early vs. late acknowledgement and worker failure?](#4-early-vs-late-acknowledgement-and-worker-failure)
- [5. How do you tune concurrency, prefetch, and fairness?](#5-how-do-you-tune-concurrency-prefetch-and-fairness)
- [6. Can concurrent Celery workers share an in-memory cache?](#6-can-concurrent-celery-workers-share-an-in-memory-cache)
- [7. Progress, cancellation, cleanup, and deduplication?](#7-progress-cancellation-cleanup-and-deduplication)
- [8. How do you verify the pipeline?](#8-how-do-you-verify-the-pipeline)
- [References](#references)

## 1. How would you process a 16 GB CSV without running out of memory?

Stream records or use bounded chunks, select only needed columns, transform incrementally, spill intermediates to disk/object storage, and stream output if the renderer supports it. Input bytes are not the same as peak memory: strings, DataFrames, copies, group-bys, renderers, and concurrency can multiply the footprint.

```python
import csv
from itertools import islice

def batches(rows, size):
    if size <= 0:
        raise ValueError("size must be positive")
    while chunk := list(islice(rows, size)):
        yield chunk

with open("input.csv", newline="", encoding="utf-8") as source:
    for chunk in batches(csv.DictReader(source), 10_000):
        # process and persist this bounded chunk; don't append all results to a list
        process_chunk(chunk)
```

**Dig deeper:** group-by/global sort may need external sorting or a DB/analytical engine. CSV quoted fields can span lines, so arbitrary byte splitting is unsafe without format-aware boundaries. How does the PDF library buffer pages/fonts/images?

## 2. Design an asynchronous export pipeline

```text
API -> validate tenant/quota -> durable job + enqueue intent -> 202 job ID
Coordinator -> immutable input manifest/version -> bounded chunk tasks
Workers -> per-chunk artifact + durable checkpoint
Finalizer -> verify all chunks -> assemble artifact -> mark complete -> notify
Download -> authorize owner -> short-lived object-storage URL
```

Messages should carry IDs/object references, not a giant DataFrame or a 16 GB payload. A manifest names chunk identity, input snapshot/version, schema, and integrity information. Publish the final artifact only after it is complete and verified.

| Granularity | Benefit | Cost |
|---|---|---|
| One huge task | Simple ordering | Long recovery, large peak memory, coarse progress |
| Many tiny tasks | Fine retries and parallelism | Broker/scheduler overhead and expensive merge |
| Bounded chunks | Balance retry cost and throughput | Need manifest, checkpoint, and finalization design |

**Dig deeper:** how do you prevent two finalizers publishing different results? What is consistency if the source dataset changes during export?

## 3. Celery broker vs. worker vs. result backend?

Broker transports task messages; worker executes them; result backend stores task state/results when configured. Result backend state alone should not be your complete business audit/workflow model.

```python
@app.task(bind=True, acks_late=True, max_retries=4)
def render_chunk(self, job_id, chunk_id):
    try:
        # Must be idempotent: stable artifact/checkpoint identity and atomic state.
        return render_and_checkpoint(job_id, chunk_id)
    except TemporaryStorageError as error:
        raise self.retry(exc=error, countdown=min(60, 2 ** self.request.retries))
```

This fragment needs real error classification, jitter, I/O deadlines, and job ownership/cancellation checks. `max_retries=4` means up to four retries after the initial attempt, not four total attempts. A successful function return does not by itself make every external effect exactly-once.

**Dig deeper:** what persists if the result backend expires? How do you reconcile Celery state with application state? Use primitive/versioned task arguments; avoid unsafe serializers for untrusted producers.

## 4. Early vs. late acknowledgement and worker failure?

| Policy | Benefit | Failure behavior |
|---|---|---|
| Early ack | Avoid re-executing a task merely because execution was interrupted | Started work can be lost unless application recovery exists |
| Late ack | Ack after task execution | Duplicate work possible; certain worker-loss cases still need explicit settings |
| Explicit retry | Schedule a new attempt on classified failure | Must preserve operation identity and bound attempts |

Celery documents that even with `acks_late`, some child-process termination cases are acknowledged; `task_reject_on_worker_lost` changes selected behavior and can cause loops for deterministic crashes. Broker transport/visibility timeout also matters. [Celery task semantics](https://docs.celeryq.dev/en/stable/userguide/tasks.html).

**Dig deeper:** a worker writes a PDF then dies before checkpoint/ack. On retry, can it safely detect/reuse the artifact? An OOM-causing task should not redeliver endlessly without a bounded repair policy.

## 5. How do you tune concurrency, prefetch, and fairness?

Start with measured per-task CPU, memory, I/O waits, downstream limits, and failure recovery time. Worker pool choice affects execution behavior; do not assume Python threads accelerate CPU-bound Python code. Prefetch can let workers reserve tasks ahead of execution, causing unfair distribution for long jobs.

| Control | Benefit | Cost |
|---|---|---|
| Lower prefetch | Better distribution of long tasks | Can reduce throughput for tiny tasks |
| Separate queues/pools | Protect interactive/short work from bulk jobs | Capacity allocation and routing complexity |
| Per-tenant concurrency | Prevent noisy neighbors | Fair scheduler/state required |
| Worker recycling | Contain memory growth temporarily | Warmup/replay; not a leak fix |

**Dig deeper:** total memory includes concurrent tasks × per-task peak plus worker/runtime/cached data. Is queue admission bounded, or are you just moving overload into a broker?

## 6. Can concurrent Celery workers share an in-memory cache?

An ordinary dictionary is local to one process. Prefork workers may inherit pages initially, but updates are not a coherent shared dictionary; writes can break copy-on-write sharing. Across hosts, process memory is separate.

| Sharing method | Fit | Tradeoff |
|---|---|---|
| Process-local cache | Reuse within one process | Duplicate memory and uneven hit rates |
| Redis | Shared small metadata/results | Serialization/network/memory; not ideal for arbitrary huge datasets |
| Shared immutable file/memory mapping | Large local read-mostly data | Node scope, lifecycle, format, and platform constraints |
| Object store + manifests | Durable cross-host artifacts | Download/I/O and local caching policy |

**Resume drill:** identify exactly how your task cache worked, its scope, data size, ownership, expiry, and crash recovery. Do not describe a local cache as cluster-shared unless that was implemented.

## 7. Progress, cancellation, cleanup, and deduplication?

Persist completed chunk IDs or counters updated atomically; derive progress from a stable manifest. Cancellation should be durable and checked at safe points. Killing a process is not the same as reversing side effects.

Use deterministic artifact keys and atomic checkpoint transitions. Final assembly needs its own claim/version to prevent duplicate publication. Clean up abandoned temporary files/uploads, expired artifacts, and stale checkpoints through an ownership-aware retention job.

**Dig deeper:** counting retries as new completed work inflates progress. What if a user cancels while final upload completes? Define which terminal state wins and whether the artifact remains accessible.

## 8. How do you verify the pipeline?

Measure job latency and oldest queued age, chunk duration/variance, memory peak/slope, broker payload size, retries, incomplete manifests, finalization failures, and cost. Test large quoted CSV fields, malformed input, encoding issues, skewed chunks, full temp disk, storage timeout, worker kill, OOM, duplicate delivery, and cross-tenant download access.

**Interview answer structure:** input size and constraints → bounded processing → task boundaries → checkpoint/idempotency → capacity → failure recovery → measured evidence.

## References

- [Celery tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html)
- [Celery optimization and prefetch](https://docs.celeryq.dev/en/stable/userguide/optimizing.html)
- [Python CSV](https://docs.python.org/3/library/csv.html)
- [Pandas scaling to large datasets](https://pandas.pydata.org/docs/user_guide/scale.html)
