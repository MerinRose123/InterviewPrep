# Gordian: interview questions and answers

[Architecture, stack, and contributions](Interview_Guide.md) · [All projects](../README.md)

**How to practice:** “Experience answer” uses the supplied career materials. “Design answer” explains how to approach a problem and does not claim that Gordian implemented it. Recall prompts identify details needed for a stronger personal answer.

## Project and ownership

### 1. Tell me about Gordian.

**Experience answer:** Gordian was a single-tenant copying-detection application for a client with a large equipment-related reference CSV. Users uploaded competitor documents, and we cleaned and analyzed the data and used document similarity scores to identify possible plagiarism and generate findings for client review and possible legal follow-up. I worked on Python analysis using Pandas/NumPy, visualization of 50,000+ points using Matplotlib/MongoDB, and Celery PDF reporting over 16 GB+ datasets with cached data reuse.


### 2. What did you personally contribute?

**Experience answer:** My documented contributions include implementing piracy-detection processing, analyzing and visualizing piracy data, engineering the Celery reporting pipeline, and caching expensive dataset loads. The project used a single-tenant Flask backend and Docker; I cannot currently confirm whether Nginx was used in Gordian. I should explain one specific module or change for each claim and distinguish my implementation from team architecture decisions.

### 3. Walk me through the architecture.

**Experience answer:** The project combined an Angular frontend, Flask backend, Docker-packaged services, and EC2 hosting. MongoDB was the project's database for application and analysis data. PostgreSQL was not used. Python, Pandas, and NumPy supported piracy analysis, Matplotlib supported visualization, and Celery generated reports using WeasyPrint with reuse of expensive loaded data. The exact service boundaries, production Redis configuration, and connection paths need confirmation; the guide's diagram reconstructs those logical responsibilities.

### 4. What was the business value?

**Experience answer:** Automated piracy-level detection and visual analysis supported product decision-making, while asynchronous reporting and caching reduced repeated expensive data loading. I can substantiate scale as 50,000+ analysis points and 16 GB+ reporting datasets. I do not have a verified accuracy improvement or customer revenue result.

### 5. What was your hardest technical challenge?

**Experience answer:** A strong documented example is PDF generation from large CSV datasets under memory constraints. Repeated loads took around 30 minutes, so I engineered Celery execution and a shared LRU cache to reuse loaded data. The article documents the in-memory base-task cache pattern; production worker settings and the large-file parsing strategy still need confirmation. I should not invent an out-of-memory incident or a final latency number.

## Piracy detection and machine learning

### 6. How did the software detect piracy?

**Experience answer:** The client maintained a large base CSV containing equipment details and related information. When a competitor document was uploaded, we cleaned and analyzed the data and used similarity scores between documents to identify possible plagiarism. Python, Pandas, and NumPy were used for analysis. The remaining details are the specific cleaning steps, TF-IDF configuration, threshold, and score aggregation formula. Public Gordian construction-cost data context is linked in the guide; it does not independently establish our private implementation.


### 7. How did similarity scoring identify possible plagiarism?

**Experience answer:** We used TF-IDF with cosine similarity. After cleaning and analyzing the inputs, the fitted TF-IDF model represented reference content and competitor documents in a shared vector space. Cosine similarity measured their similarity to identify possible plagiarism. Development used Jupyter Notebook and Anaconda with Pandas, NumPy, and Matplotlib. TF-IDF fitting learns corpus vocabulary and term weights without requiring plagiarism labels. See the [algorithm explanation](Interview_Guide.md#algorithm-tf-idf-with-cosine-similarity).


### 8. How would you decide between classification and regression?

**Design answer:** First define the target. Discrete labels such as low/medium/high suggest classification, potentially with an ordinal relationship. A continuous measured quantity suggests regression. A risk score may require calibration and threshold selection. The phrase “piracy level” alone does not determine which formulation Gordian used.

### 9. How would you evaluate a piracy detector?

**Design answer:** For a comparison system, validate known copied and independent examples, inspect match quality, and define how record/field matches aggregate into the reported copying amount. State the denominator and distinguish generic equipment descriptions from distinctive copied content. If a trained classifier was involved, evaluate its precision/recall and held-out performance as well. No detection-accuracy figure is supplied.


### 10. How would you prevent data leakage?

**Design answer:** Separate training and evaluation before fitting preprocessing. Keep related records for the same document or entity in one partition where appropriate, and use time-based evaluation if deployment predicts future activity. Exclude features that reveal outcomes available only after prediction. The project's historical split and feature pipeline remain unverified.

### 11. How would you handle class imbalance?

**Design answer:** Inspect class frequencies and evaluate minority-class precision/recall rather than relying on accuracy. Compare weighting, threshold changes, and resampling within the training partition. Choose the approach using validation data and business costs, then assess on an untouched test set. Avoid resampling before splitting because related samples can leak across partitions.

### 12. How did Pandas and NumPy help?

**Experience answer:** I used them for data cleaning, analytics, and processing that supported document similarity scoring. Pandas provides labeled tabular transformations, while NumPy supports numerical arrays and vectorized operations. I should add a real transformation I implemented. Neither tool by itself identifies the model, and vectorization can increase peak memory if it creates large temporary arrays.

### 13. How did you use Matplotlib?

**Experience answer:** I analyzed and visualized more than 50,000 data points using Matplotlib and MongoDB to support product decisions. I need to recall the actual chart and the decision it informed. I should not invent a dashboard layout, a trend, or a specific business conclusion.

### 14. What if detection quality degrades over time?

**Design answer:** Track changing input distributions, missing fields, prediction distributions, and delayed quality metrics when labels arrive. Investigate data-quality changes and shifting piracy behavior before retraining. Version model and preprocessing together, compare against a validated baseline, and make rollback possible. Gordian's monitoring and retraining mechanisms are not documented.

## Large-data processing, Celery, and caching

### 15. Why did you use Celery?

**Experience answer:** Report generation was long-running work over large datasets. Celery supported background execution instead of tying completion to a synchronous web request. I engineered the asynchronous PDF pipeline. Celery does not itself reduce memory usage or remove repeated loads; data reuse addressed that separate bottleneck.

### 16. How did you process a 16 GB file with limited RAM?

**Experience answer:** The documented implementation used a Celery pipeline with reusable in-memory/shared LRU caching under memory constraints. The exact parsing and memory-management strategy is not recorded. A concrete [recommended memory and caching design](Interview_Guide.md#recommended-design-memory-worker-concurrency-and-invalidation) explains chunked preparation, versioned sparse artifacts, memory-based concurrency, and invalidation. **Design follow-up:** I would assess column selection, data types, chunked aggregation, intermediates, and concurrency. I would not claim that we used chunking or held the entire dataset in RAM without confirmation.

### 17. What does an LRU cache do?

**Answer:** It retains reusable values and evicts the least recently used entry when capacity is exceeded. Our documented use avoided repeated expensive data loads. A cache's effectiveness depends on reuse and capacity; large entries also require a memory budget, since an entry-count limit alone may be unsafe.

### 18. How was your cache shared across Celery tasks?

**Experience answer:** I used Celery's LRUCache through a custom base task to reuse expensive reference resources within a worker process, as described in my [article](https://merin-rose-tom.medium.com/caching-in-celery-using-lrucache-357053251e96). Independent worker processes do not automatically share this memory.

**Recommended configuration:** Start with one long-lived heavy-comparison process, cache the fitted TF-IDF vectorizer and bounded prepared reference partitions, and reuse them across uploads. Use versioned cache keys and measure peak memory before increasing concurrency. This configuration is the selected design recommendation; exact historical settings remain unverified. [Detailed design](Interview_Guide.md#recommended-design-memory-worker-concurrency-and-invalidation).


### 19. Was Redis the dataset cache?

**Experience answer:** The article uses Redis as the broker, while the dataset-reuse pattern uses an in-memory cache. Redis should not be described as the large-dataset cache on this evidence. Production broker/result-backend configuration still needs confirmation.


### 20. How would you prevent concurrent cache misses from causing repeated loads?

**Design answer:** Coordinate one load per cache key while other tasks wait or reuse the completed result. Bound waiting and handle loader failure, cancellation, and stale ownership. In a multi-process or multi-host deployment, a local thread lock is insufficient. The actual Gordian miss-coordination mechanism needs confirmation.

### 21. How would you choose cache keys and invalidation?

**Design answer:** For this single-tenant system, use reference-dataset identity/version and preprocessing version for reusable base data. Include uploaded-document identity when caching comparison-specific results. Invalidate or change identity when inputs change. LRU eviction controls capacity, not correctness or freshness. The production key and invalidation rules need confirmation.


### 22. What would you measure to validate the optimization?

**Design answer:** Compare equivalent workloads before and after the change: load count, load time, cache hit rate, end-to-end report latency, queue delay, peak process/host memory, and failure rate. Record cold-cache and warm-cache behavior separately. **Experience boundary:** the documented result is elimination of redundant loads taking around 30 minutes; no final latency or memory-reduction percentage is supplied.

### 23. How would you make report tasks safe to retry?

**Design answer:** Use a durable logical report identity, track attempts separately, and ensure retried execution cannot publish conflicting outputs. Generate into a temporary artifact and atomically expose the completed result using the storage system's suitable mechanism. Recheck permissions and dataset version. Exact Celery acknowledgment, retry, and deduplication settings in Gordian are unknown.

### 24. What if a worker crashes halfway through a report?

**Design answer:** Make incomplete work distinguishable from successful output, record failure/progress durably, and apply bounded retries for recoverable errors. Retrying from the beginning may be acceptable; checkpointing is useful only when recovery savings justify its complexity. Redelivery depends on broker and worker configuration, so I cannot promise it from the presence of Celery alone.

### 25. How would you scale report generation?

**Design answer:** Measure the limiting resource first: memory, CPU, source throughput, database load, or queue backlog. Bound worker concurrency using peak task memory, separate heavy reporting from latency-sensitive tasks where appropriate, and apply backpressure. More workers can duplicate large cached datasets and exhaust memory, so adding concurrency can make this workload worse.

### 26. How did you generate the PDFs?

**Experience answer:** Celery tasks generated PDFs from large CSV datasets with cached data reuse. We used WeasyPrint for PDF generation. The exact template/data preparation, output storage, and download mechanism still need to be recalled.

## Backend, databases, and security

### 27. Which database did Gordian use?

**Experience answer:** Gordian used MongoDB as its database; it did not use PostgreSQL. MongoDB stored the application's persisted data, including analysis-related records. **Design follow-up:** Compare document and relational models based on access patterns, consistency constraints, and query needs.

### 28. Was Gordian multi-tenant?

**Experience answer:** Gordian was single-tenant, as I have clarified directly. Older career materials describe multi-tenancy, but that attribution should not be used for this project. Multiple authorized users and document uploads belong to the same client application. Access checks for reference data, competitor uploads, and reports still matter.


### 29. Which backend framework did Gordian use?

**Experience answer:** Gordian used Flask. Django was not involved in this project. My direct clarification supersedes older career-material stack attributions. I should explain the actual Flask routes, application structure, and Celery integration when discussing implementation.

### 30. What did Docker contribute, and was a reverse proxy used?

**Experience answer:** Docker packaged backend components and standardized development environments. I do not currently remember whether Gordian used Nginx, so I would not claim a specific reverse-proxy configuration. If asked about a hypothetical design, I can explain where a reverse proxy might sit without presenting it as a historical implementation.

### 31. How would you secure a report API?

**Design answer:** Authenticate the caller, authorize the operation and requested data for the relevant files and comparison job, validate inputs, and enforce report ownership again when retrieving output. Check permissions for the requested reference version, uploaded file, and report. Protect sensitive content in logs and cache keys, and bound request size and job creation. Gordian's historical authentication and permission mechanisms need confirmation.

### 32. Which tests would you prioritize?

**Design answer:** Test data preparation with missing/malformed values; detection behavior against known examples; upload/report access control in database and cache paths; cold/warm cache equivalence; concurrent cache misses; stale dataset versions; task retries; and incomplete report publication. Use small fixtures plus representative large-data memory checks. The existing EventOps pytest coverage claims should not be attributed to Gordian without evidence.

### 33. How would you investigate a slow report?

**Design answer:** Separate queue wait, source loading, preprocessing, analysis, rendering, and output publication. Check cache misses and invalidation, data-size changes, database queries, memory pressure, and concurrency. Compare with a known workload and change the measured bottleneck. I should use a remembered incident if asked what I actually debugged.

## Behavioral answers and evidence

### 34. Explain the caching work using STAR.

**Experience answer:** “The reporting pipeline processed 16 GB+ CSV datasets under memory constraints, and redundant data loads took around 30 minutes. My task was to support asynchronous reports and reduce repeated work. I engineered the Celery pipeline and implemented a shared LRU cache for reusable loaded data. That eliminated redundant loads across concurrent tasks.” The published pattern is a process-local base-task cache; I still need production worker settings and validation evidence for deeper follow-up.

### 35. Did you improve operational efficiency by 15% on Gordian?

**Experience answer:** My resume and LinkedIn report a 15% operational-efficiency improvement in the InApp role. The supplied evidence does not explicitly tie that metric to Gordian or define its baseline. I should confirm the attribution and measurement before using it as a Gordian result.

### 36. What would you improve today?

**Design answer:** I would first inspect the current bottlenecks and correctness risks. For this workload, useful candidates are memory-aware concurrency, dataset versioning, coordinated cache loading, file/report access regression tests, and report-stage observability. I would prioritize observed failure modes; these suggestions do not establish that the original system lacked those features.

### 37. What should you say when you cannot recall a detail?

**Practice answer:** “I can explain my contribution and the documented result, but I need to verify that particular implementation detail. Here is how I would reason about the design.” Then clearly separate experience from a proposed approach. Do not substitute a familiar model, PDF library, cache package, or deployment pattern for the one actually used.

## MongoDB design and performance

The [MongoDB deep dive](MongoDB_Interview_Deep_Dive.md) includes an illustrative schema, validation, mongosh/PyMongo reads, aggregation, indexes, explain plans, and pagination code. These are proposed examples; the historical collection design remains unverified.

### 38. How would you compare MongoDB with PostgreSQL for a similar system?

**Experience answer:** Gordian used MongoDB, not PostgreSQL. **Hypothetical design comparison:** Equipment records can have varying nested attributes, and comparison outputs can fit a document model. I would choose based on access patterns, consistency needs, and operational cost. PostgreSQL with JSONB could also work. [Tradeoffs](MongoDB_Interview_Deep_Dive.md#1-why-mongodb-why-not-postgresql).

### 39. How did you create the schema?

**Design answer:** Define access patterns and document boundaries first, then choose stable identity/version fields, bounded embedded attributes, references, validation, and indexes. One possible design uses reference records, comparison jobs, and candidate matches as separate collections. This is not a recovered Gordian schema. [Schema and creation code](MongoDB_Interview_Deep_Dive.md#2-how-do-you-create-a-schema-in-mongodb).

### 40. How do you fetch data from MongoDB in Python?

**Answer:** Use PyMongo filters and projections with `find_one` for a single result or iterate a `find` cursor for multiple results. Apply sort and limit at the server. Match BSON types correctly, especially ObjectId identifiers. [Python and mongosh examples](MongoDB_Interview_Deep_Dive.md#3-how-do-you-fetch-data).

### 41. When do you embed and when do you reference?

**Design answer:** Embed small bounded attributes read with their parent. Reference large or independently queried relationships. For example, keep equipment attributes with a reference record, but put potentially many candidate matches in their own collection. Avoid an indefinitely growing matches array in one job document. [Model](MongoDB_Interview_Deep_Dive.md#2-how-do-you-create-a-schema-in-mongodb).

### 42. How do you prevent inconsistent document types?

**Design answer:** Normalize inputs in application code and enforce important types and ranges with collection validation. A validator can require ObjectId job identifiers and numeric scores in a defined range. It does not establish that a similarity score correctly measures copying. [Validator example](MongoDB_Interview_Deep_Dive.md#2-how-do-you-create-a-schema-in-mongodb).

### 43. How do you choose indexes?

**Design answer:** Start with an actual query. For one job's top matches, evaluate a compound index on comparison ID, descending score, and descending ID. Confirm the plan and measured benefit. Extra indexes also cost writes and storage. [Index examples](MongoDB_Interview_Deep_Dive.md#5-which-indexes-would-you-create).

### 44. How do you debug a slow MongoDB query?

**Design answer:** Capture its filter, sort, projection, result limit, and realistic parameter values. Use execution statistics to inspect examined keys/documents, returned rows, and sort behavior. Then assess server load and application/network time. Fix and compare the same workload. [Diagnosis and explain code](MongoDB_Interview_Deep_Dive.md#6-how-do-you-handle-slow-queries).

### 45. Does IXSCAN mean a query is optimized?

**Answer:** No. An index scan may still examine many keys or require expensive filtering and sorting. Interpret examined counts relative to returned results and expected selectivity. Measure real application latency as well. [Explain interpretation](MongoDB_Interview_Deep_Dive.md#6-how-do-you-handle-slow-queries).

### 46. How do you avoid loading a large result into memory?

**Design answer:** Push filtering/projection to the database, bound UI results, and iterate cursors for exports or processing. A batch size controls transfer batches; it does not cap the entire result set. Avoid collecting an unbounded cursor into a Python list. [Cursor example](MongoDB_Interview_Deep_Dive.md#3-how-do-you-fetch-data).

### 47. How do you paginate large match results?

**Design answer:** Use a deterministic sort and continuation values from the last score/ID pair instead of increasingly large offsets. Keep completed results immutable or version them so updates do not move rows during pagination. [Pagination code](MongoDB_Interview_Deep_Dive.md#7-how-do-you-paginate-without-a-large-skip).

### 48. How do you calculate a report summary in MongoDB?

**Design answer:** Match one comparison, then group candidate records for counts and similarity statistics. Multiple candidates can refer to the same uploaded row, so define deduplication and the denominator before presenting a copying amount. [Aggregation code](MongoDB_Interview_Deep_Dive.md#4-how-do-you-aggregate-results).

## Redis versus RabbitMQ

### 49. Why did you use Redis instead of RabbitMQ for Gordian?

**Interview answer:** “We used Redis as the Celery broker. For this workflow, the broker needed to dispatch small comparison/report jobs, while workers performed the expensive processing. Redis was a reasonable fit for that straightforward task-queue requirement. The large reference data was not the task message, and our reusable dataset cache was an in-process Celery LRUCache, not Redis. RabbitMQ was also a valid option; I would consider it when messaging-specific routing and delivery-control requirements justify a dedicated broker.”

**Evidence boundary:** Redis as broker is documented in the published example. The small-message architecture is the selected recommendation, and the original team's selection rationale and production settings are not recovered. Present this as why the choice fits the workload; do not claim a benchmark, lower cost, or a documented RabbitMQ evaluation.

| Concern | Redis with Celery | RabbitMQ with Celery | Relevance to Gordian |
|---|---|---|---|
| Role | In-memory data store used as broker; can separately be a result backend | Dedicated message broker | Both support Celery task dispatch |
| Task payload | Good fit for small task messages | Also suitable for small task messages | Send IDs/versions, not CSVs, DataFrames, or PDF bytes |
| Routing | Celery queue routing is available | Exchanges and bindings provide richer broker-level routing | A few worker queues do not alone require complex routing |
| Redelivery | Celery Redis transport uses visibility timeout for unacknowledged deliveries | Consumer acknowledgements and requeueing; acknowledgment-timeout policies also matter | Align failure handling with long-running jobs |
| Persistence | Redis persistence/HA and memory configuration must be deliberate | Queue type, durability, message persistence, and replication must be deliberate | Neither name alone establishes loss-free processing |
| Publisher confirmation | Do not assume RabbitMQ-style publisher-confirm semantics | Supports publisher confirms separately from consumer acknowledgements | Broker acceptance is distinct from task completion |
| Result storage | Can additionally hold task state/results if configured | A result backend is a separate choice; Celery supports an RPC backend | Redis broker use does not prove Redis result-backend use |
| Dataset caching | Separate from this project's in-process LRUCache | Also separate from the worker's local LRUCache | Switching brokers would not inherently remove the cache optimization |
| Operational choice | Can avoid adding another broker if Redis is already operated for suitable purposes | Adds a messaging-specific service if none already exists | Actual deployment and operational costs need evidence |

Sources: [Celery broker overview](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html), [Celery Redis transport](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html), [RabbitMQ acknowledgements and confirms](https://www.rabbitmq.com/docs/confirms). Technical behavior should be checked against the versions deployed; these links describe current documentation.

### 50. What is the main Redis caveat for long-running Celery tasks?

**Design answer:** With late acknowledgments, a task can remain unacknowledged during processing. If that exceeds the Redis transport's visibility timeout, it may be redelivered while the original execution is still running. Check acknowledgment mode, task runtime bounds, visibility settings, and retries together. Early acknowledgment has a different risk: a worker crash after acknowledgment can lose that delivery. Make report publication idempotent and track job status durably rather than claiming exactly-once execution. Simply making the timeout very large delays recovery after failures. [Redis caveats](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#caveats).

### 51. Would RabbitMQ guarantee that each report runs exactly once?

**Answer:** No. Publisher confirms acknowledge broker acceptance, while consumer acknowledgements address delivery processing. Failures and retries can still produce duplicates, so the application needs idempotent report generation/publication and durable job identity. Neither a broker choice nor an acknowledgement proves that the client received a completed PDF. [RabbitMQ confirms](https://www.rabbitmq.com/docs/confirms).

### 52. When would you choose RabbitMQ instead?

**Design answer:** When requirements call for richer exchange/binding routing, messaging-specific operational controls, and explicit publisher-confirm workflows, I would evaluate RabbitMQ against the required queue type, replication, throughput, and failure model. I would also check its consumer acknowledgement timeouts for long tasks. I would not switch merely because the input CSV is large: input size belongs to the worker/storage design when messages carry only identifiers.

## MongoDB versus Amazon SQS

### 53. Why use MongoDB instead of Amazon SQS if documents can be processed through SQS?

**Interview answer:** “MongoDB supported analysis data and queries. Amazon SQS handles asynchronous message delivery, so it would be an alternative at the messaging layer rather than a replacement for MongoDB. A worker could receive a document-processing request from SQS and still store its analysis results in MongoDB.”

| Requirement | MongoDB | Amazon SQS |
|---|---|---|
| Store analysis records for repeated retrieval | Document database | Messages retained until deletion or retention expiry |
| Query by document ID, score, or other fields | Indexed filters and queries | No equivalent general database querying |
| Aggregate findings for reports | Aggregation operations | Consumer performs analysis and persists results elsewhere |
| Dispatch processing requests | Separate queue generally appropriate | Managed message queue |
| Role in a possible Gordian design | Analysis persistence and retrieval | Alternative to Redis's Celery broker role, subject to transport requirements |

**Possible design, not historical deployment:** Store uploaded files in file/object storage; queue a small message containing file/job identifiers; let a worker perform cleaning and similarity scoring; persist analysis records/results in MongoDB. SQS transports processing requests, not a queryable document repository. Its ability to carry messages about documents does not replace database storage or file storage.

If an interviewer says “document streaming,” clarify whether they mean SQS, S3, or Amazon DocumentDB: these address messaging, object storage, and document-database workloads respectively. Do not claim Gordian used these AWS services without evidence.

Sources: [AWS SQS overview](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html), [MongoDB overview](https://www.mongodb.com/docs/manual/).

## Final rehearsal checklist

- Deliver the 60-second introduction, then draw the architecture from the companion guide.
- Explain the difference between background execution and avoiding repeated dataset loads.
- Explain the published cache pattern and its process boundary; recover production pool settings and one real transformation.
- Explain TF-IDF fitting and cosine similarity; recover cleaning operations, configuration, threshold, and evaluation examples.
- Prepare one genuine failure/debugging story with the change and verification you performed.
- Keep 50,000+ analysis points, 16 GB+ reporting inputs, and 30-minute repeated loads as distinct metrics.

Sources and evidence boundaries are recorded in the [companion guide](Interview_Guide.md#8-sources-and-remaining-confirmations).


---

## Senior-engineer mock interview: Gordian (deep-dive drills)

These drills are meant to be spoken aloud. The **project fact** is what you can describe as implemented. The **scenario** is an interviewer-imposed change or failure; its solution is a design answer, not a claim about production Gordian.

### Drill G1 — Your 16 GB report is taking 30 minutes just to load data. Walk me through the fix.

**Interviewer:** "Start from the user clicking Generate. Where is the expensive work, and what did you change?"

**Project fact:** Gordian generated PDF reports asynchronously with Celery, processing datasets larger than 16 GB. Repeated loading of reference data could cost roughly 30 minutes. A custom Celery base-task implementation reused loaded data with an in-memory LRU cache.

**Strong answer:** "I would first separate request latency from worker execution. The Flask endpoint should enqueue a report job rather than parse the entire reference dataset in the HTTP request. The worker needs the reference dataset, which was expensive to load repeatedly. We reused previously loaded data through an LRU cache attached to the task/worker execution path, so later tasks handled by the same worker process could avoid that load. The important boundary is process memory: two Celery worker processes do not share one Python cache. I would measure load time, cache hit rate, peak RSS, total report latency, and worker concurrency rather than claiming caching alone fixes memory pressure."

**Interviewer pushes:** "Why not just put 16 GB in Redis?"  
**Answer:** "Redis is a separate in-memory service and would introduce another large memory allocation, serialization, network transfer, and eviction problem. Redis was useful for Celery task messaging; that does not mean it was our dataset cache. For datasets that large, I would also compare streaming/chunking and a versioned on-disk representation."

**Interviewer pushes:** "What if you start eight worker processes?"  
**Answer:** "Each process can load its own copy, so worst-case memory grows roughly with concurrent loaded copies, not just with task count. I'd cap concurrency based on measured resident memory and memory headroom. More workers can make throughput worse by multiplying cold loads or causing swapping/OOM."

**Whiteboard:** Flask request → task identifier → Redis broker → Celery worker → versioned reference-data load/cache → analysis/report rendering → report artifact.

**What to defend:** Cache scope, eviction behavior, stale data, worker restarts, memory budget, and actual before/after load measurements. Don't call this a distributed shared cache.

### Drill G2 — Two reports use different versions of the reference CSV. How do you prevent incorrect reuse?

**Interviewer:** "Your LRU cache already has the reference data. A new CSV is uploaded while reports are running. What happens?"

**Design answer:** "The cache key must represent immutable dataset identity, not a generic name such as 'latest'. I'd assign each uploaded reference dataset a version or content hash. The report job records the version it was created against. The worker loads and caches by that version; new jobs can use the new version while in-flight jobs continue with the old one. Old cache entries can be evicted after they are no longer needed. The result should record its source dataset version for reproducibility."

**Interviewer pushes:** "What if a report job is retried on another worker?"  
**Answer:** "That worker may have a cold cache. It should still retrieve the same immutable dataset version and produce a logically equivalent result. A cache hit is an optimization, not a correctness dependency."

**Design sketch:**
\`\`\`python
# Illustrative design, not historical Gordian code.
cache_key = (dataset_version, parser_version)
data = local_lru.get(cache_key)
if data is None:
    data = load_reference_dataset(dataset_version)
    local_lru.put(cache_key, data)
\`\`\`

**What to defend:** Immutable input references, reproducible reports, cache invalidation, and idempotent retries.

### Drill G3 — Celery says the task ran twice. Can the customer receive duplicate reports?

**Interviewer:** "The worker generated the PDF, then crashed before acknowledging the message."

**Design answer:** "Task queues may redeliver work; exactly-once execution should not be assumed. I'd give each requested report a durable job ID and use an idempotency key derived from the request or an explicit client key. A worker claims the job, writes output to a temporary/versioned artifact, and atomically publishes one final report reference when complete. A retried task checks whether the final result already exists before doing unnecessary work. A state transition should be conditional on the expected prior state so two workers cannot both publish conflicting final results."

**Interviewer pushes:** "Does Redis or Celery guarantee exactly once?"  
**Answer:** "No. Queue acknowledgement and application side effects are separate boundaries. I would design for at-least-once execution and idempotent publication, then test crash-after-upload and retry-after-timeout cases."

**Design sketch:** Job states \`PENDING → RUNNING → COMPLETED\` or \`FAILED\`; each transition has a stable job ID, attempt number, and completion artifact reference. The exact job-state storage is a design decision; Gordian's database was MongoDB, not PostgreSQL.

### Drill G4 — The report service crashes on a 16 GB dataset. What is your debugging plan?

**Interviewer:** "CPU is high, memory is climbing, and reports are failing."

**Strong answer:** "I would establish whether memory is rising during CSV parsing, Pandas transforms, document similarity calculations, chart generation, or PDF rendering. I'd correlate per-process RSS with worker concurrency and cache occupancy. Loading a 16 GB CSV can consume far more than 16 GB in memory after object conversion and intermediate DataFrames. I'd test smaller representative input, profile allocations, inspect data types and unnecessary copies, and consider \`read_csv(chunksize=...)\`, selected columns, and streaming aggregation where algorithmically valid."

**Interviewer pushes:** "Would you increase worker count?"  
**Answer:** "Not before finding the bottleneck. If memory-bound, more workers can increase OOMs. If CPU-bound, I would evaluate parallelism within a memory budget. If I/O-bound, I would examine storage and repeated reads."

**Follow-up test:** Run a controlled 1-, 2-, and 4-worker benchmark with the same dataset; report throughput, peak RSS, cold/warm latency, and failure rate. These are proposed tests, not historical results.

### Drill G5 — Explain the piracy-detection algorithm without hiding behind 'machine learning'.

**Interviewer:** "A competitor document shares common industry terms with the reference. Why isn't that automatically piracy?"

**Project fact:** Gordian's analysis involved Python, Pandas/NumPy and text similarity using TF-IDF and cosine similarity.

**Strong answer:** "TF-IDF converts documents into weighted term vectors, emphasizing terms that are informative within the corpus. Cosine similarity measures how closely the weighted vectors align; it does not prove copying or intent. Shared domain vocabulary, boilerplate, short documents, and preprocessing choices can create false positives. I'd explain tokenization, normalization, stop-word choices, the corpus used to fit IDF, and how a threshold is calibrated against reviewed examples."

**Interviewer pushes:** "What if two documents have the same meaning but different wording?"  
**Answer:** "A sparse lexical TF-IDF representation may miss paraphrases. Semantic embeddings are one possible alternative, but they change explainability, evaluation, and cost; I would not claim we deployed embeddings."

**Interviewer pushes:** "What metric would you show the client?"  
**Answer:** "Precision and recall against reviewed examples, a confusion matrix at a chosen threshold, and examples of false positives/negatives. A high cosine score alone is not a validated accuracy metric."

### Drill G6 — Why MongoDB, and what indexes would you actually add?

**Interviewer:** "A user opens a report and filters matches by dataset, document, and descending similarity score. Show me the query."

**Project fact:** MongoDB was Gordian's only database. The following document structure is a design exercise, not a recovered production schema.

\`\`\`javascript
db.matches.find(
  { dataset_version: "v12", document_id: "doc-42" },
  { document_id: 1, score: 1, matched_reference: 1 }
).sort({ score: -1 }).limit(50)
\`\`\`

**Design answer:** "For that access pattern I would test a compound index on \`{dataset_version: 1, document_id: 1, score: -1}\`. Equality filters come first and the sort follows. I'd use \`explain('executionStats')\` to inspect keys/documents examined and whether a blocking sort remains. The index should be justified by measured query frequency and write overhead."

**Interviewer pushes:** "Why not offset pagination at page 10,000?"  
**Answer:** "Large skips can be costly. I would use cursor/keyset pagination with a stable tie-breaker such as \`_id\` and an index that supports the ordering."

### Drill G7 — How do you handle a partial report when the worker fails?

**Interviewer:** "The PDF is 90% generated and the instance restarts."

**Design answer:** "Treat the output as incomplete until a final publish step succeeds. Write to a temporary path/object, verify completion, then publish the final artifact and mark the job complete. On retry, detect an existing complete artifact or restart from a checkpoint if the report pipeline supports it. Clean up abandoned temporary artifacts. I'd avoid exposing partial PDFs under the final download URL."

**Interviewer pushes:** "How do you know the report used the correct reference version?"  
**Answer:** "Persist the immutable dataset version with the job and include it in the report metadata and logs. The output should be traceable to the inputs."

### Drill G8 — You have ten minutes with the hiring manager. Which Gordian story do you choose?

**Answer structure (90 seconds):** "The user-facing problem was expensive report generation over large reference datasets. My contribution was the asynchronous Celery reporting pipeline and a worker-local LRU reuse mechanism that avoided repeated roughly 30-minute data loads. The non-obvious trade-off is that a Python cache is process-local, so adding workers can multiply memory consumption. If redesigning today, I'd benchmark cold/warm paths, enforce dataset-version keys, and make retries and output publication idempotent."

**Follow-up questions to rehearse:** "What was the cache capacity?" "What evicted an entry?" "What happened after a worker restart?" "How did you measure improvement?" "Why not use a streaming pipeline?" Give your actual recalled details; don't substitute hypothetical values.
