# Gordian — Engineering challenges

[Project guide](01_Project_Overview.md) · [Interview Q&A](05_Interview_QA.md) · [MongoDB deep dive](../../Cheatsheets/MongoDB_NoSQL.md)

## Interview opening (90 seconds)

“Gordian was a single-tenant copying-detection and reporting application. Users submitted competitor documents that were compared with a large equipment-related reference dataset. I worked on Python-based cleaning and analysis using Pandas and NumPy, TF-IDF and cosine similarity, analysis and visualization using Matplotlib and MongoDB, and asynchronous PDF generation using Celery and WeasyPrint. A major engineering challenge was processing reports against datasets larger than 16 GB under memory constraints. I used an in-process Celery LRU cache to avoid repeated reference-data loads that could take around 30 minutes.”

## Analysis workflow and TF-IDF

The confirmed business workflow is reference-to-upload comparison:

1. Maintain the client's large base CSV containing equipment-related records.
2. Accept another document supplied by the client, originating from a competitor.
3. Clean and analyze the data, then compute similarity scores between the reference content and uploaded documents to identify possible plagiarism.
4. Present similarity-based findings and analysis, with PDF reports generated using WeasyPrint.
5. Let the client review the findings and decide whether further action is required.

Merin confirms data cleaning, other data-analysis methods, and similarity scoring between documents. Python, Pandas, and NumPy are documented processing tools. The exact extraction/parsing method, record alignment, specific cleaning operations, TF-IDF fitting corpus/configuration, threshold and aggregation formula are still unverified. A copying percentage needs a defined denominator: matched reference records, matched upload records, or matched fields can produce different numbers. These are possible interpretations, not recovered implementation details.

The resume's “machine learning” description does not establish that the system used supervised learning. Document similarity scoring and a trained/fitted model are now directly confirmed; supervised classification is not established. Training-label and classification-metric questions apply only if that was the implementation.

### Algorithm: TF-IDF with cosine similarity

Gordian used **TF-IDF with cosine similarity** to identify possible plagiarism between reference content and competitor documents. Data cleaning and analysis prepared the inputs. The fitted TF-IDF model learned vocabulary and inverse-document-frequency weights from a corpus; documents were represented in a shared feature space and compared using cosine similarity.

TF-IDF fitting does not require labeled copying examples. Cosine similarity measures vector similarity; it is not itself a trained classifier or a calibrated copying probability. A score should not automatically be interpreted as the literal percentage of content copied.

Use the same fitted vectorizer for both sides of a comparison. The specific fitting corpus, cleaning operations, n-gram configuration, saved model format, threshold, and document/section aggregation remain implementation details to recover.

References: [TF-IDF](https://scikit-learn.org/stable/modules/feature_extraction.html), [cosine similarity](https://scikit-learn.org/stable/modules/metrics.html#cosine-similarity).

**Why lexical similarity?** Exact matching misses small wording changes. TF-IDF/cosine is explainable and efficient for lexical similarity; semantic embeddings may capture paraphrases but add model, infrastructure, and evaluation cost. A candidate-filtering stage can reduce comparisons before more expensive scoring. Generic equipment language can cause false positives, so inspect matched evidence and review examples.

### Development environment

Development and analysis used **Jupyter Notebook and Anaconda**, with **Pandas, NumPy, and Matplotlib** for data preparation, numerical processing, exploration, and visualization.

## Reporting and cache implementation

### Documented problem and contribution

Report generation involved CSV datasets larger than 16 GB under memory constraints. Repeated loading could take around 30 minutes. Merin engineered Celery-based asynchronous report generation and a shared LRU cache to reuse data across concurrent tasks and eliminate redundant loads.

Celery moved long-running reporting out of synchronous request execution. Caching addressed repeated data preparation. These solve different problems: asynchronous execution alone does not reduce dataset memory or loading cost.

### Explain the cache precisely

Merin identified the [published caching article](https://merin-rose-tom.medium.com/caching-in-celery-using-lrucache-357053251e96) as the implementation reference. It uses `celery.utils.functional.LRUCache`, a configured `RESOURCE_CACHE`, and a custom `ResourceTask` base exposing `shared_resource_data` to child tasks. The example sets an entry limit of 10 and uses Redis as broker. These example values are not independently verified production settings.

**Process boundary:** The described cache is in-memory. Reuse through a common base task does not create distributed shared memory. Independent prefork worker processes can retain separate caches, so warm-cache reuse applies within the process holding the cached resource. Historical worker settings belong in the [recall checklist](../README.md#details-to-recall).

For large datasets, cache entry count alone is not a sufficient memory budget. DataFrame memory, intermediate arrays, copied slices, worker concurrency, and PDF rendering all contribute to peak memory. The 16 GB input size does not establish that the entire file was retained in RAM.



### Recommended design: memory, worker concurrency, and invalidation

This is a recommended approach for the workload, not a reconstruction of production settings. The best chunk size and concurrency depend on measured RAM, text lengths, vocabulary size, and task peaks.

**Selected approach:** Follow the published `ResourceTask` / Celery `LRUCache` pattern with one long-lived process initially assigned to the heavy comparison queue. Reuse the fitted TF-IDF vectorizer and bounded prepared reference-vector partitions within that process. Prepare the reference CSV in chunks, persist reusable artifacts, and load them on cache misses. Redis remains the broker in the published pattern. Use versioned keys and measure peak memory before increasing concurrency. This is the agreed recommendation; exact historical production settings remain unverified.

**Cache lifecycle:** A task looks up `(reference_version, cleaning_version, vectorizer_version, partition_id)`. On a hit it reuses the local resource; on a miss it loads the prepared artifact and retains it if capacity permits. Different uploads reuse the same reference key. Publish new immutable versions for data/model changes, pin running jobs to their original versions, and retire old versions after their jobs finish. Bound cache memory as well as entry count: the blog's ten-entry example is not a ten-entry production recommendation for large partitions.


**Prepare once per reference version.** Read selected CSV columns in bounded chunks with explicit types, clean each chunk, and persist versioned processed partitions. Do not accumulate chunks into a list and concatenate them back into a full DataFrame. Preserve equipment codes as strings where leading zeros matter. Example column names below are illustrative:

```python
import pandas as pd

def prepare_reference(csv_path, write_partition):
    for part, frame in enumerate(pd.read_csv(
        csv_path,
        usecols=["record_code", "description"],
        dtype={"record_code": "string", "description": "string"},
        chunksize=50_000,  # Starting point; tune against measured peak memory.
    )):
        frame["description"] = (
            frame["description"].fillna("").str.strip().str.replace(
                r"\s+", " ", regex=True
            )
        )
        write_partition(part, frame)  # Persist now; do not retain all frames.
```

Chunked reading limits input working memory; it does not make every later operation out-of-core. TF-IDF fitting also needs a memory plan. Use a bounded vocabulary and a repeatable corpus iterator where feasible; profile fitting separately. If vocabulary/statistics still exceed the budget, use an explicit multi-pass/out-of-core preparation strategy rather than fitting an unrelated vectorizer per chunk. Transform reference partitions with the **same fitted vectorizer**, save sparse features, and version their row mappings. Score upload batches against reference blocks, retaining only needed top matches or incremental summaries. Avoid materializing a dense all-upload-by-all-reference similarity matrix. Exact global statistics may require more than a top-k summary.

**Keep task messages small.** Queue upload IDs, reference/model versions, and processing parameters. Store source data and artifacts durably; Redis carries task messages and, if desired, small coordination/status data. Cache the fitted vectorizer and bounded reference-feature blocks in worker-local memory rather than assuming a 16 GB DataFrame fits or is shared across processes.

**Bound concurrency by measured memory.** Start the heavy comparison queue with one process. Increase only after observing peak task memory and downstream capacity. For a process-local cache, a conservative sizing condition is:

`processes × (worker baseline + cached artifacts + peak task working memory) + other host memory + safety reserve <= host RAM`

A separate reporting queue prevents WeasyPrint rendering from competing with similarity computation; include both queues in the host budget. Set prefetch conservatively, for example `worker_prefetch_multiplier = 1`, while recognizing that early acknowledgments can still allow an extra reserved task per process. Worker recycling can control retained memory growth but discards warm caches; a memory-per-child setting is not a hard mid-task RAM cap. [Celery optimization](https://docs.celeryq.dev/en/stable/userguide/optimizing.html).

**Use versioned cache identities.** A base-artifact key can be `(reference_version, cleaning_version, vectorizer_version, partition_id)`. A comparison-result key additionally includes upload content hash, scoring configuration/threshold, and aggregation version. A PDF cache additionally depends on report-template version. Keep base-data cache keys independent of upload ID so different comparisons can reuse the base artifacts.

**Invalidate through immutable versions.** Write a new reference/model version to a separate location, finish and validate its artifacts, then atomically publish a ready manifest. Pin each job to that manifest. New jobs use the new version; running jobs keep their original version. Retire old artifacts after active jobs no longer depend on them. TTL/LRU eviction controls retention; it does not replace version correctness. Bound cache bytes, not just entry count, and coalesce concurrent loads where necessary. Independent processes may still have independent copies.

**Validate the design.** Measure cold/warm load time, peak process and host RAM, cache hits/evictions, queue wait, comparison time, PDF time, and failure rate on representative inputs. CSV file size alone does not predict DataFrame or sparse-feature memory.

References: [Pandas CSV reading](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html), [large-data processing](https://pandas.pydata.org/docs/user_guide/scale.html), and the TF-IDF references above. The chunk count and cache-key names here are proposed examples.

### Broker choice: Redis versus RabbitMQ

Redis dispatched Celery work in the published implementation pattern. The in-process LRUCache handled reusable resources separately. The [broker comparison and interview answers](05_Interview_QA.md#redis-versus-rabbitmq) explain why Redis fits small task messages, when RabbitMQ is worth evaluating, and how long-task visibility/acknowledgement settings affect retries. The original selection rationale is not documented.

## Challenge: asynchronous report generation

**Project components:** Flask backend, Celery workers, WeasyPrint, and PDF output.

**Interviewer:** “Why not generate PDFs inside the Flask request?”

Report rendering is long-running and memory-intensive. Moving it to Celery decouples request latency from job completion and allows worker-specific resource limits. The client can submit a report request and later retrieve job status/output.

**Trade-offs:** Background execution improves responsiveness but introduces a broker, retry behavior, monitoring, and the possibility of duplicate work. WeasyPrint rendering can also consume significant memory independently of the dataset processing stage.

**Failure scenario:** Worker crashes after writing a PDF but before acknowledging the task. A retry should not publish inconsistent duplicate outputs. Use stable job IDs, temporary artifact names, atomic final publication where possible, and an explicit job state machine.

## Challenge: Redis versus RabbitMQ for Celery

**Interviewer:** “Why Redis instead of RabbitMQ?”

Redis served as the broker in the documented Celery implementation pattern. The task message should carry small identifiers or references rather than the full dataset. RabbitMQ is a strong alternative when sophisticated routing, acknowledgements, and messaging-specific controls are important.

**Trade-offs:** Redis is straightforward when already used in the stack; its delivery and redelivery behavior still needs careful configuration. RabbitMQ is a dedicated broker with richer routing and acknowledgement semantics, but it adds operational considerations. Neither broker guarantees exactly-once execution of a side-effecting PDF task.

**Follow-ups:** What happens when a task runs longer than the broker's visibility timeout? How do you handle retries? How do you avoid duplicate reports? Why is Redis the broker rather than the large dataset cache?

## Challenge: MongoDB persistence versus task queues

**Project components:** MongoDB was the project's database; Celery and Redis handled background task execution and messaging. PostgreSQL was not used.

**Interviewer:** “Why use MongoDB, and why not SQS?”

MongoDB persisted application and analysis data. Amazon SQS is a message-delivery service, not a substitute for querying persisted analysis results. Compare technologies by the problem they solve rather than treating them as interchangeable.

**Trade-offs:** Flexible documents help with evolving analysis output, but indexes, document growth, and aggregation cost still matter. Relational modeling may be preferable for strongly constrained transactional workflows. A queue decouples producers and workers but does not replace persistent analytical storage.

**Follow-ups:** What indexes help a query filtered by comparison ID and score? How would you paginate large result sets? How do you prevent duplicate comparison records after retries?

## Challenge: false positives and explainability

**Interviewer:** “A competitor's document contains common equipment terms. Your detector flags it as copying. What would you do?”

Inspect normalization, candidate selection, TF-IDF vocabulary, term weighting, and the match threshold. Evaluate on known independent and copied examples. Provide evidence-level matches rather than a single unexplained score, and make clear that similarity is an indicator for review rather than a legal conclusion.

**Trade-offs:** Lower thresholds improve recall but increase review workload. Higher thresholds reduce false positives but can miss paraphrased or partial copying. Evaluate with the business cost of each error type.

## Challenge: data changes while reports are running

**Interviewer:** “A new reference CSV is uploaded while an old report is still processing. Which data version should the result use?”

Give each report an explicit reference-dataset version and use it throughout analysis and rendering. Version the cache key with the dataset/preprocessing version. Publish new versions atomically and allow old in-flight jobs to complete against their pinned version, subject to retention and memory budgets.

**Trade-off:** Version pinning improves reproducibility but temporarily retains multiple datasets. Immediate invalidation saves memory but can break long-running jobs or mix results from different inputs.

## Rapid-fire scenarios

| Scenario | Strong answer direction |
|---|---|
| Every Celery task spends 30 minutes loading data | Reuse process-local prepared reference data; examine worker lifetime and cache scope |
| Multiple worker processes exhaust RAM | Bound concurrency, account for per-process cache duplication, profile peak memory |
| CSV changes but cache still serves old data | Dataset-versioned keys and explicit invalidation |
| Worker dies after writing report | Idempotent artifact publication and durable job status |
| Two jobs request the same expensive reference load | Coordinate per-key loading at the correct process boundary |
| Similarity scores are high for generic terms | Inspect TF-IDF weights, normalization, threshold, and evaluation examples |
| MongoDB queries become slow | Check query shape, indexes, cardinality, explain plans, and payload size |
| User expects report immediately | Return a job ID, expose progress, and notify or poll for completion |
| Broker redelivers a task | Assume at-least-once behavior and make side effects repeatable |
