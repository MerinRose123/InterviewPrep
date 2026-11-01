# Gordian — Engineering challenges

[Project guide](Project_Reference.md) · [Interview Q&A](05_Interview_QA.md) · [MongoDB deep dive](../../Cheatsheets/MongoDB.md)

## Interview opening (90 seconds)

“Gordian was a single-tenant copying-detection and reporting application. Users submitted competitor documents that were compared with a large equipment-related reference dataset. I worked on Python-based cleaning and analysis using Pandas and NumPy, TF-IDF and cosine similarity, analysis and visualization using Matplotlib and MongoDB, and asynchronous PDF generation using Celery and WeasyPrint. A major engineering challenge was processing reports against datasets larger than 16 GB under memory constraints. I used an in-process Celery LRU cache to avoid repeated reference-data loads that could take around 30 minutes.”

## Challenge: comparing competitor documents with reference data

**Pipeline:** Competitor document → text/data normalization → TF-IDF representation in a compatible feature space → cosine similarity → candidate matches → analysis and reporting.

**Interviewer:** “Why TF-IDF and cosine similarity rather than exact matching?”

Exact matching misses small wording changes; TF-IDF weights terms based on their frequency in documents and the broader corpus. Cosine similarity compares vector direction, helping identify similar content despite different document lengths. It does not understand meaning the way a semantic embedding model does, and generic equipment descriptions can cause false positives.

**Trade-offs:** TF-IDF is relatively explainable and efficient for lexical similarity. Embeddings may capture paraphrases but increase model, infrastructure, and evaluation complexity. A hybrid pipeline can first narrow candidates and then apply a more expensive comparison.

**Follow-ups:** What preprocessing matters? How do you handle numeric specifications and model identifiers? How do you pick a threshold? How do you distinguish repeated common phrases from copying? How do you aggregate matches into a document-level score?

## Challenge: handling 16 GB+ reference/reporting data

**Interviewer:** “Your input is bigger than available RAM. How do you process it?”

Start with the memory budget and the real access pattern. A CSV's on-disk size is not its in-memory footprint; parsing can create multiple objects and intermediate copies. For sequential aggregation, chunked reads and streaming operations can cap memory. For repeated similarity comparisons, prepare reusable reference artifacts, restrict loaded columns/types, and consider sparse representations or partitioning. Bound worker concurrency so multiple tasks do not each load a large copy.

**Trade-offs:** Streaming saves memory but may increase passes over data. Preprocessing improves repeated-query latency but requires storage, versioning, and refresh. More worker processes can reduce throughput if memory pressure causes swapping or crashes.

**Whiteboard:** Show memory consumed by worker process + parsed reference data + TF-IDF vectors + report rendering + concurrent tasks.

## Real challenge: expensive repeated data loading

**Project contribution:** Repeated reference-data loads could take approximately 30 minutes; the Celery LRU caching pattern reused expensive resources across tasks.

**Interviewer:** “How was the cache shared?”

The cache was attached to a custom Celery base-task pattern and reused within a long-lived worker process. It is **not** automatically shared across independent operating-system processes or machines. This distinction matters when concurrency is increased.

**Trade-offs:** In-process caching avoids network round trips and repeated parsing, but duplicates memory across workers and loses contents on restart. Redis or an external cache enables cross-process access, but large Python objects may be expensive to serialize and move. A versioned prepared artifact on shared storage is another option.

**Follow-ups:** What is the cache key? How do you invalidate it when the reference CSV changes? What happens on a cold start? What if several tasks miss simultaneously? How do you avoid evicting a huge object under memory pressure?

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

## Interview delivery pattern

Anchor the answer in the real pipeline: **competitor input → analysis → data reuse → asynchronous reporting**. Then explain the bottleneck, the technical choice, the alternative, and what happens on retry or scale. Your strongest personal story is the large-data/Celery/cache optimization; use it as the foundation for deeper system-design questions.
