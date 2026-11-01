# Gordian — scaling and failure scenarios

[Architecture](02_Architecture_and_Data_Flow.md) · [Challenges](03_Engineering_Challenges.md) · [Interview Q&A](05_Interview_QA.md)

Gordian was a single-tenant Flask/MongoDB application with Celery reporting and WeasyPrint. The large-data workload and cache optimization are documented; the following mechanisms are interview design exercises unless explicitly confirmed in the project guide.

## Worker count increases but throughput falls

**Invariant:** peak aggregate working memory must stay within the host/container budget.

**Walkthrough:** Separate CSV size on disk from parsed data, sparse features, intermediate results, and PDF rendering memory. A process-local cache may be duplicated in each worker. Measure peak resident memory per workload before choosing concurrency; isolate expensive tasks from lightweight jobs and bound pending work.

**Tradeoff:** More processes can improve CPU utilization until duplicated data and memory pressure dominate. Chunking helps input processing but does not automatically bound TF-IDF fitting or a dense similarity matrix.

**Verify:** compare cold/warm runs and different concurrency levels. Record peak RSS, restarts/OOMs, queue age, reports completed per minute, and tail completion time.

## Many tasks miss the reference cache simultaneously

**Invariant:** repeated tasks must reuse the correct reference version without uncontrolled duplicate loading.

**Walkthrough:** Explain the process-local cache boundary first. Within a process, coordinate loading if concurrent execution requires it; across processes, consider prepared versioned artifacts or another explicitly shared design. Cache keys should include reference/preprocessing versions. Do not describe Redis as the historical dataset cache without evidence.

**Tradeoff:** A shared external cache adds serialization and transfer cost; a local cache duplicates memory and disappears on restart.

**Verify:** test cold start, concurrent misses, eviction, and dataset replacement. Measure duplicate loads, load latency, cache memory, and hit rate; historical production values remain unverified.

## A report finishes writing, then the worker dies before acknowledgement

**Invariant:** retry must not publish conflicting final outputs for the same logical job.

**Walkthrough:** Use a stable job identity, temporary artifacts, explicit completion state, and controlled final publication. Before repeating an expensive render, check whether a valid output already exists. Task acknowledgement policy affects redelivery and must match the actual worker/broker setup.

**Tradeoff:** Late acknowledgement can support recovery but increases duplicate-execution risk. A broker does not provide exactly-once PDF side effects.

**Verify:** kill a worker at rendering and publication boundaries. Check artifact integrity, duplicate outputs, retry counts, and cleanup of temporary files.

## Reference data changes halfway through a comparison

**Invariant:** each result must correspond to a defined reference dataset and fitted feature space.

**Walkthrough:** Pin dataset, preprocessing, and vectorizer versions for a job. Transform both sides with the same fitted vectorizer. Retain artifacts needed by in-flight work and retire old versions after their retention window.

**Tradeoff:** Retaining multiple versions consumes storage/cache capacity; switching mid-job makes results hard to reproduce.

**Verify:** publish a new reference version during an old job, then reproduce the old result. Record the versions with the report rather than inferring them from current state.

## MongoDB results grow and report listing slows

**Walkthrough:** Identify the real query shape before proposing indexes. Consider a comparison/job identifier plus stable sort fields, bounded result pages, and projection of required fields. Avoid unbounded match arrays in one document. The [MongoDB guide](../../Cheatsheets/MongoDB.md) contains illustrative schemas, not recovered production collections.

**Verify:** inspect query execution statistics with representative data, pagination ties, retries, and duplicate writes. Balance query gains against index write/storage costs.

## Similarity output looks convincing but is wrong

**Walkthrough:** Check text normalization, common phrases, vocabulary, numeric identifiers, reference/upload alignment, threshold, and document-level aggregation. TF-IDF cosine similarity is not a calibrated copying probability. Inspect matched evidence and evaluate known copied/independent examples before changing thresholds.

**Verify:** cover generic equipment descriptions, partial copying, empty input, and changed source versions. Discuss false positives/negatives without inventing historical accuracy metrics.

For a real experience answer, start with the [reporting/cache story](01_Project_Overview.md#star-answer-reporting-optimization), then distinguish remembered implementation from these proposed safeguards.
