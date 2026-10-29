# Gordian: MongoDB schema, queries, and performance

[Project guide](Interview_Guide.md) · [Interview Q&A](Interview_Questions_and_Answers.md)

**Evidence boundary:** MongoDB use for Gordian analysis is documented. Its actual collections, indexes, and original selection rationale are not recovered. Everything below is an illustrative design for the confirmed single-tenant reference-CSV versus competitor-document workflow. Use it to explain design choices; replace examples with remembered production details before saying “we implemented this.”

**Confirmed processing context:** The backend was Flask, PDF generation used WeasyPrint, and data cleaning/analytics supported document similarity scoring. The record-pair schema below is an illustrative storage design, not confirmation of the granularity of the original document-level scores.

## 1. Why MongoDB? Why not PostgreSQL?

**Interview answer:** “MongoDB was used with our analysis data. A document model can fit equipment records with varying attributes and nested comparison outputs. I would choose it when the main reads retrieve those structures together. I would not say MongoDB is automatically faster or that PostgreSQL cannot handle JSON. The actual project rationale needs confirmation.”

| Decision factor | MongoDB option | PostgreSQL option |
|---|---|---|
| Equipment types have different attributes | Nested documents with stable core fields | Relational core plus JSONB or related tables |
| Retrieve one record and its small attributes together | Embed attributes | Columns/JSONB |
| Many independent matches per comparison | Separate referenced collection | Child table with foreign keys |
| Strong relational constraints and joins dominate | More application coordination may be needed | Often a natural fit |
| Performance | Depends on workload, indexes, and document size | Also depends on workload, indexes, and query shape |

Do not justify two databases merely because the application has “structured and unstructured data.” Explain which store owns each entity and why the extra operational cost is worthwhile. The reference CSV does not have to be stored in MongoDB in order for analysis outputs to use MongoDB.

## 2. How do you create a schema in MongoDB?

Start from access patterns: fetch a reference record by version and code; list comparisons; page through one comparison's strongest matches; summarize results. Define document boundaries, types, versions, validation, and indexes around those reads. MongoDB's flexible schema still requires deliberate modeling. [Data modeling](https://www.mongodb.com/docs/manual/data-modeling/).

One possible design:

| Collection | One document represents | Important fields |
|---|---|---|
| `reference_records` | One reference CSV row | `dataset_version`, `record_code`, `description`, `attributes` |
| `comparisons` | One upload/comparison job | `reference_version`, `upload_id`, `status`, `created_at`, `algorithm_version` |
| `comparison_matches` | One candidate matched record pair | `comparison_id`, `reference_record_id`, `upload_row`, `similarity_score`, `matched_fields` |

`attributes` can vary by equipment type while identity fields stay consistent. Embed small bounded values read with the parent. Reference independently queried or unbounded related records. Do not embed every match or the complete CSV in one comparison document. [References](https://www.mongodb.com/docs/manual/data-modeling/referencing/).

Example documents in **mongosh**; these are invented data:

```javascript
use gordian_practice

const refId = ObjectId();
const comparisonId = ObjectId();

db.reference_records.insertOne({
  _id: refId,
  dataset_version: "base-v1",
  record_code: "EQ-001",
  description: "Illustrative pump equipment record",
  attributes: { category: "pump", power_kw: 7.5 },
  schema_version: 1
});

db.comparisons.insertOne({
  _id: comparisonId,
  reference_version: "base-v1",
  upload_id: "upload-demo-001",
  status: "completed",
  created_at: new Date(),
  algorithm_version: "illustrative-v1"
});
```

Collections can be created explicitly, including validation. This example belongs in a fresh practice database before inserting matches:

```javascript
db.createCollection("comparison_matches", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["comparison_id", "reference_record_id", "upload_row",
                 "similarity_score", "matched_fields"],
      properties: {
        comparison_id: { bsonType: "objectId" },
        reference_record_id: { bsonType: "objectId" },
        upload_row: { bsonType: "int", minimum: 1 },
        similarity_score: {
          bsonType: "double", minimum: 0, maximum: 1
        },
        matched_fields: {
          bsonType: "array", items: { bsonType: "string" }
        }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
});

db.comparison_matches.insertOne({
  comparison_id: comparisonId,
  reference_record_id: refId,
  upload_row: NumberInt(1),
  similarity_score: NumberDouble("0.93"),
  matched_fields: ["description", "attributes.power_kw"]
});
```

This validates shape/types/range, not whether referenced documents exist or the algorithm is correct. A similarity score of 0.93 is sample data, not “93% proven copying.” Existing collections can have validators changed with `collMod`; plan cleanup of old documents separately. [Schema validation](https://www.mongodb.com/docs/manual/core/schema-validation/).

## 3. How do you fetch data?

Use filters, projections, sorting, and limits rather than fetching all documents and filtering in Python. BSON `ObjectId` values must be queried as `ObjectId`, not their string representation.

```javascript
// Exact lookup: pair this with the unique index in section 5.
db.reference_records.findOne({
  dataset_version: "base-v1", record_code: "EQ-001"
});

// Strongest candidate matches for one comparison.
db.comparison_matches.find(
  { comparison_id: comparisonId, similarity_score: { $gte: 0.8 } },
  { reference_record_id: 1, upload_row: 1, similarity_score: 1 }
).sort({ similarity_score: -1, _id: -1 }).limit(50);
```

The same read with **PyMongo**. Requires `pymongo` and a `MONGODB_URI` environment variable pointing to a practice database deployment:

```python
import os
from bson import ObjectId
from pymongo import MongoClient, DESCENDING

client = MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=5000)
db = client["gordian_practice"]

# A real application receives and validates the requested comparison ID.
job = db.comparisons.find_one({"upload_id": "upload-demo-001"}, {"_id": 1})
if job is None:
    raise LookupError("Comparison not found")
comparison_id = ObjectId(str(job["_id"]))

cursor = (
    db.comparison_matches.find(
        {"comparison_id": comparison_id, "similarity_score": {"$gte": 0.8}},
        {"reference_record_id": 1, "upload_row": 1, "similarity_score": 1},
    )
    .sort([("similarity_score", DESCENDING), ("_id", DESCENDING)])
    .limit(50)
    .batch_size(50)
    .max_time_ms(2000)
)
try:
    for match in cursor:
        print(match)  # Replace with application processing.
finally:
    cursor.close()
    client.close()
```

`find_one` returns a document or `None`; `find` returns a cursor. Iterate large result sets rather than materializing `list(cursor)`. Batch size affects transfer batches; limit caps returned records. A server query timeout bounds work but is not an optimization. In a web service, manage a reusable client per application process rather than opening one per request. [PyMongo reads](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/find/).

## 4. How do you aggregate results?

For an illustrative summary, filter one job first, then group its stored candidate matches:

```javascript
db.comparison_matches.aggregate([
  { $match: { comparison_id: comparisonId } },
  { $group: {
      _id: "$comparison_id",
      candidate_pairs: { $sum: 1 },
      average_similarity: { $avg: "$similarity_score" },
      strongest_similarity: { $max: "$similarity_score" }
  } }
]);
```

These are candidate-pair statistics. Multiple reference candidates can match the same uploaded row, so neither pair count nor average similarity is automatically the copying amount. Define deduplication and the denominator separately. A report-level summary can be materialized after completion when repeated reads justify it, with explicit invalidation/versioning.

## 5. Which indexes would you create?

Indexes follow actual query shapes:

```javascript
// Equality lookup and uniqueness within each reference version.
db.reference_records.createIndex(
  { dataset_version: 1, record_code: 1 }, { unique: true }
);

// Equality on job, then descending score and deterministic tie-breaker.
db.comparison_matches.createIndex(
  { comparison_id: 1, similarity_score: -1, _id: -1 },
  { name: "job_score_page" }
);
```

The second index targets the top-match query above. Index order matters; querying by score alone does not use the leading job field to narrow the scan. Equality-sort-range is a guideline: selective range filters can justify another order. Each additional index consumes space and adds write work. Confirm benefit rather than indexing every field. [Index ordering](https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/).

## 6. How do you handle slow queries?

**Interview answer:** “First I identify the exact slow operation and representative parameters. I inspect its execution plan and examined-versus-returned counts, then check indexing, sorting, result size, and server resources. I change the measured bottleneck and compare equivalent workloads before and after.”

```javascript
db.comparison_matches.find(
  { comparison_id: comparisonId, similarity_score: { $gte: 0.8 } },
  { reference_record_id: 1, upload_row: 1, similarity_score: 1 }
).sort({ similarity_score: -1, _id: -1 })
 .limit(50)
 .explain("executionStats");
```

| Observation | Interpretation / next action |
|---|---|
| `COLLSCAN` for a selective lookup | Check missing/incompatible index and query field types |
| `IXSCAN` but many keys examined | Index may be poorly selective or mismatched to predicates |
| Many documents examined for few returned | Investigate residual filters and index fit |
| Blocking sort stage | Check whether index ordering can satisfy the requested sort |
| Few examined documents but high API latency | Investigate network, connection pool, application work, and payload size |
| Slow only under concurrency | Check CPU, disk, memory pressure, contention, and competing tasks |

Read `nReturned`, `totalDocsExamined`, `totalKeysExamined`, and the winning plan together. An index scan alone is not proof of efficiency; a collection scan can be appropriate for a small collection or a query returning most records. `executionStats` executes the read; use representative bounded requests. Explain bypasses the plan cache, so also measure real request latency. [Explain results](https://www.mongodb.com/docs/manual/reference/explain-results/).

### A concrete before/after narrative to practice

**Illustrative problem:** A report screen loads every candidate pair into Python, filters by job, sorts, and shows 50 rows. As historical data grows, transfers and memory use grow too.

**Change:** Filter by `comparison_id` in MongoDB, project needed fields, sort/limit server-side, and evaluate `job_score_page`. Measure the same job on equivalent data with cold/warm conditions recorded. Do not invent a percentage improvement or claim this incident happened in Gordian.

If the index already fits, investigate expensive aggregations, large documents, unbounded arrays, disk pressure, and excessive concurrency. Cache only after understanding query cost and freshness requirements. Sharding is a later capacity decision, not the first response to a missing index. [Query optimization](https://www.mongodb.com/docs/manual/core/query-optimization/).

## 7. How do you paginate without a large skip?

For descending score order, retain the last row's score and `_id` as a continuation key. The next page uses the same job filter, threshold, sort, and projection:

```javascript
// Values from the final row of the preceding page; sample only.
const lastScore = 0.93;
const lastId = ObjectId("000000000000000000000001");

db.comparison_matches.find({
  comparison_id: comparisonId,
  similarity_score: { $gte: 0.8 },
  $or: [
    { similarity_score: { $lt: lastScore } },
    { similarity_score: lastScore, _id: { $lt: lastId } }
  ]
}).sort({ similarity_score: -1, _id: -1 }).limit(50);
```

This is a design for immutable completed comparison results. If scores change while paging, rows can move across page boundaries. Use a stable result version when consistent pagination matters. Avoid promises that any particular page is constant-time; inspect the actual plan.

## 8. Short follow-up answers

**Can MongoDB do joins?** `$lookup` combines collections, but decide whether embedding, separate queries, or a join fits the workload. References are identifiers, not automatically enforced foreign keys.

**Does flexible schema mean no migrations?** No. Additive optional fields may be easy, but changing types or meaning still requires version-aware readers, backfills, validation changes, and compatible deployment order.

**Would you store 16 GB in one document?** No. Model individual records and keep large source files outside an ordinary single document. File storage and metadata have different responsibilities; this is a proposed design, not confirmation of Gordian storage.

**Would more indexes always help?** No. Measure read benefits against write cost and storage. A projection reduces transferred fields but does not guarantee an index-covered query.

**What should you recover from the real project?** One actual document, one collection name, one filter, one index, the PyMongo/ODM library used, and one measured query issue. These turn a design answer into a personal implementation story.

## 9. Why MongoDB rather than Amazon SQS?

These solve different requirements: MongoDB stores queryable analysis records; SQS delivers messages to processing workers. In a possible architecture, file storage holds the upload, SQS carries its file/job ID, and a worker writes analysis results to MongoDB. SQS could replace the Redis broker role after evaluating Celery transport requirements; it does not replace MongoDB queries and aggregations. See the [comparison and interview answer](Interview_Questions_and_Answers.md#mongodb-versus-amazon-sqs). This is an architectural comparison, not a claim that Gordian used SQS.
