# Large Data and Background Processing Interview Cheat Sheet

[Study index](README.md) · Related: [messaging](../Cheatsheets/Kafka.md), [memory profiling](Memory_Profiling_Performance.md), [workflows](Workflow_Orchestration.md).

This guide owns provider-independent pipeline design. For Celery-specific APIs and configuration, follow the linked technology guide.

## Contents

- [1. How would you process a 16 GB CSV without running out of memory?](Large_Data_Background_Processing.md#how-would-you-process-a-16-gb-csv-without-running-out-of-memory)
- [2. Design an asynchronous export pipeline](Large_Data_Background_Processing.md#design-an-asynchronous-export-pipeline)
- [Execution capacity and shared data](#execution-capacity-and-shared-data)
- [7. Progress, cancellation, cleanup, and deduplication?](Large_Data_Background_Processing.md#progress-cancellation-cleanup-and-deduplication)
- [8. How do you verify the pipeline?](Large_Data_Background_Processing.md#how-do-you-verify-the-pipeline)
- [References](#references)

## How would you process a 16 GB CSV without running out of memory?

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

## Design an asynchronous export pipeline

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

## Execution capacity and shared data

Choose task boundaries and concurrency from measured CPU, memory, I/O, recovery cost, and downstream capacity. Admission control and tenant fairness belong to the pipeline design; adding workers cannot fix an overloaded database or unbounded per-task memory.

Choose whether reusable data is process-local, shared by a host, or stored as durable cross-host artifacts. The scope must match input-version consistency and recovery requirements. Pin jobs to immutable dataset versions and treat cache loss as a recoverable cold start.

Celery broker/result roles, acknowledgement, pool/prefetch settings, and process-cache mechanics are documented once in [Celery](../Cheatsheets/Celery.md). Redis commands and server durability are in [Redis](../Cheatsheets/Redis.md).

## Progress, cancellation, cleanup, and deduplication?

Persist completed chunk IDs or counters updated atomically; derive progress from a stable manifest. Cancellation should be durable and checked at safe points. Killing a process is not the same as reversing side effects.

Use deterministic artifact keys and atomic checkpoint transitions. Final assembly needs its own claim/version to prevent duplicate publication. Clean up abandoned temporary files/uploads, expired artifacts, and stale checkpoints through an ownership-aware retention job.

**Dig deeper:** counting retries as new completed work inflates progress. What if a user cancels while final upload completes? Define which terminal state wins and whether the artifact remains accessible.

## How do you verify the pipeline?

Measure job latency and oldest queued age, chunk duration/variance, memory peak/slope, broker payload size, retries, incomplete manifests, finalization failures, and cost. Test large quoted CSV fields, malformed input, encoding issues, skewed chunks, full temp disk, storage timeout, worker kill, OOM, duplicate delivery, and cross-tenant download access.

**Interview answer structure:** input size and constraints → bounded processing → task boundaries → checkpoint/idempotency → capacity → failure recovery → measured evidence.

## References

- [Python CSV](https://docs.python.org/3/library/csv.html)
- [Pandas scaling to large datasets](https://pandas.pydata.org/docs/user_guide/scale.html)
