# Search Systems Interview Cheat Sheet

[Study index](README.md) · Related: [database](../Cheatsheets/Database.md), [messaging](../Cheatsheets/Kafka.md), [RAG](RAG_AI_Agents.md).

Examples use OpenSearch-style REST APIs. Verify exact syntax/features for your OpenSearch/Elasticsearch version; these products are not interchangeable in every detail.

## Contents

- [1. Why a search engine instead of SQL LIKE?](#1-why-a-search-engine-instead-of-sql-like)
- [2. Explain shards, replicas, and node roles](#2-explain-shards-replicas-and-node-roles)
- [3. Text vs. keyword and mapping choices?](#3-text-vs-keyword-and-mapping-choices)
- [4. How do queries and tenant filtering work?](#4-how-do-queries-and-tenant-filtering-work)
- [5. Is a successful write immediately searchable?](#5-is-a-successful-write-immediately-searchable)
- [6. How do you keep search synchronized with the database?](#6-how-do-you-keep-search-synchronized-with-the-database)
- [7. Reindex without downtime: what is the full plan?](#7-reindex-without-downtime-what-is-the-full-plan)
- [8. What do you monitor and test?](#8-what-do-you-monitor-and-test)
- [References](#references)

## 1. Why a search engine instead of SQL LIKE?

Search engines maintain inverted indexes mapping terms to documents, with analysis and ranking. They support full-text relevance, tokenization, aggregations, and specialized query types. A relational DB may be sufficient for structured filters or moderate full-text workloads; a separate search cluster adds synchronization and operations cost.

| Approach | Prefer when | Cost |
|---|---|---|
| SQL index/full-text features | Existing DB meets query/scale needs | DB load and engine-specific search features |
| Search engine | Relevance, complex text, aggregations, independent scaling | Eventual projection, cluster capacity, mapping/reindex lifecycle |
| Vector/hybrid retrieval | Semantic similarity plus filters/text | Embedding/index cost and evaluation |

**Dig deeper:** search ranking is not an authorization mechanism. Why should authoritative order/payment state usually stay in the transactional system?

## 2. Explain shards, replicas, and node roles

An index is split into primary shards; replicas copy shard data and can support availability/read throughput. Cluster management elects authority for cluster metadata; shard primaries coordinate writes to their shard copies. Data nodes store/search data; coordinating work fans queries out and merges results. Exact roles/configuration depend on the product/version.

**Failure:** a node loss can leave replica allocation unavailable or trigger recovery. Replicas on the same failure domain do not protect against that domain failing.

| Decision | Advantage | Tradeoff |
|---|---|---|
| More primary shards | Parallelism/distribution | Overhead and expensive fan-out/merge |
| More replicas | Failure tolerance/read options | More storage and write replication |
| Dedicated coordinating capacity | Isolate heavy aggregation/merge | More nodes; not a cure for poor queries |

**Dig deeper:** adding replicas does not split one primary's write workload into independent partitions. A green cluster does not prove good latency or complete source synchronization.

## 3. Text vs. keyword and mapping choices?

```http
PUT /products-v2
Content-Type: application/json

{"settings":{"number_of_shards":3,"number_of_replicas":1},
 "mappings":{"properties":{
   "tenant_id":{"type":"keyword"},
   "title":{"type":"text","fields":{"raw":{"type":"keyword"}}},
   "updated_at":{"type":"date"},
   "source_version":{"type":"long"}
 }}}
```

`text` is analyzed for full-text matching; `keyword` suits exact filters, sorting, and many aggregations. Define analyzers and multi-fields around actual query needs. Uncontrolled dynamic fields can create mapping explosion; nested/object choices affect query semantics.

**Dig deeper:** a `term` query on analyzed text is not the same as a `match` query. Why can case/tokenization/stemming change results? Can you change a field's existing type in place? Usually you need a new mapping/index and migration.

## 4. How do queries and tenant filtering work?

```http
GET /products-read/_search
Content-Type: application/json

{"size":20,"query":{"bool":{
 "must":[{"match":{"title":"wireless keyboard"}}],
 "filter":[{"term":{"tenant_id":"tenant-7"}}]
}}}
```

The example tenant is resolved from verified server-side context; clients must not be allowed to remove/replace an enforced isolation predicate. Restrict expensive wildcard/scripts/aggregations and arbitrary query DSL exposure.

**Dig deeper:** routing by tenant can reduce fan-out but is not authorization. Hot tenants can overload routed shards. How do you paginate deep results with a stable view, for example supported point-in-time plus `search_after`?

## 5. Is a successful write immediately searchable?

Search engines are commonly near-real-time: visibility to search depends on refresh behavior. Refresh, durability/translog, replication acknowledgement, and source-database commit are separate concepts. Forcing refresh after every write can damage throughput.

| Need | Strategy | Cost |
|---|---|---|
| Immediate authoritative confirmation | Read from source / write result | Not a ranked search result |
| User waits until search visibility | Supported refresh-wait policy where appropriate | Added latency and refresh coordination |
| Normal catalog/search | Accept measured projection/refresh lag | Explain freshness to users |

**Dig deeper:** a search read after a DB commit may be stale because of CDC lag before refresh even begins. Which lag are you measuring?

## 6. How do you keep search synchronized with the database?

Use CDC/outbox/ingestion jobs with stable document IDs, source versions, deletion handling, retry, and replay. Avoid ordinary dual writes that can leave DB and search inconsistent. Handle updates arriving out of order by comparing authoritative source versions using supported write semantics.

```text
DB commit + outbox -> ingestion -> version-aware search write -> progress checkpoint
Repair: compare source/projection counts and sampled records; rebuild when necessary
```

**Dig deeper:** counts alone do not prove content equality. A delete must prevent a delayed older update resurrecting a document. What happens when the consumer replays a week of events?

## 7. Reindex without downtime: what is the full plan?

Create destination with explicit mappings/settings → snapshot/backfill → capture concurrent changes and deletions → replay/catch up with version ordering → verify correctness/lag → switch read/write aliases deliberately → retain rollback window.

```http
POST /_reindex?wait_for_completion=false
Content-Type: application/json

{"source":{"index":"products-v1"},"dest":{"index":"products-v2"}}
```

```http
POST /_aliases
Content-Type: application/json

{"actions":[
 {"remove":{"index":"products-v1","alias":"products-read"}},
 {"add":{"index":"products-v2","alias":"products-read"}}
]}
```

Reindexing alone does not continuously mirror writes/deletes during the copy. Destination settings/mappings must be created deliberately; a copy can be I/O-intensive. An alias switch does not automatically redirect an ingestion pipeline hardcoded to the old index. [Reindex reference](https://docs.opensearch.org/latest/im-plugin/reindex-data/).

**Dig deeper:** what is rollback after new writes only reached v2? Who cleans up v1 and when? How do you throttle backfill to preserve interactive search?

## 8. What do you monitor and test?

Shard allocation/recovery, heap/GC, disk watermarks, query/index latency, rejected work, ingestion lag, refresh/merge pressure, hot shards, and snapshot restoration. Inspect slow-query evidence and query plans/profiling with care for overhead.

Test node loss, unavailable replicas, disk pressure, mapping error, poison documents, stale updates, delete races, and reindex under live writes. Restore snapshots in a separate environment; replicas are not historical backups.

**Resume drill:** explain the actual cluster topology, your reindex cutover/catch-up mechanism, failure you handled, and how you measured search consistency. “Integrated a cluster” should be backed by a request/write path diagram.

## References

- [OpenSearch reindex](https://docs.opensearch.org/latest/im-plugin/reindex-data/)
- [OpenSearch index aliases](https://docs.opensearch.org/latest/im-plugin/index-alias/)
- [OpenSearch mappings](https://docs.opensearch.org/latest/mappings/)
- [OpenSearch cluster health](https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-health/)
