# Messaging and Kafka Interview Cheat Sheet

[Study index](README.md) · Related: [background jobs](Large_Data_Background_Processing_CheatSheet.md), [distributed systems](Distributed_Systems_CheatSheet.md), [microservices](Microservices_CheatSheet.md).

Kafka examples use classic consumer-group partition assignment and Kafka 4.x concepts. Client versions, group protocols, and managed services differ; verify deployed configuration instead of relying on defaults.

## Contents

- [1. Queue vs. publish/subscribe vs. retained log?](#1-queue-vs-publishsubscribe-vs-retained-log)
- [2. Explain Kafka architecture and a record's path](#2-explain-kafka-architecture-and-a-records-path)
- [3. How do keys, partitions, and consumer groups affect scaling?](#3-how-do-keys-partitions-and-consumer-groups-affect-scaling)
- [4. What do acknowledgements and replication actually guarantee?](#4-what-do-acknowledgements-and-replication-actually-guarantee)
- [5. At-most-once vs. at-least-once vs. exactly-once?](#5-at-most-once-vs-at-least-once-vs-exactly-once)
- [6. What is an offset, and when should it be committed?](#6-what-is-an-offset-and-when-should-it-be-committed)
- [7. How do retries and DLQs affect ordering?](#7-how-do-retries-and-dlqs-affect-ordering)
- [8. What do you monitor and test?](#8-what-do-you-monitor-and-test)
- [References](#references)

## 1. Queue vs. publish/subscribe vs. retained log?

| Model | Practical fit | Tradeoff |
|---|---|---|
| Work queue | One logical worker processes each job | Visibility/acknowledgement/redelivery and poison tasks |
| Pub/Sub | Broadcast live notifications | Durability/replay depend on product; disconnected subscribers may miss events |
| Retained partitioned log | Replay, stream processing, independent subscribers | Retention/storage and offset ownership need management |

Kafka retains records according to topic policy rather than deleting each record when one consumer reads it. Separate consumer groups can process the same log independently. A queue-like business workflow can be built on a log, but its retry/routing semantics must be designed.

**Dig deeper:** do you need fan-out, replay, delayed jobs, per-job acknowledgement, or all four? Why might Celery plus a task broker be simpler for scheduled exports than implementing job semantics in Kafka?

## 2. Explain Kafka architecture and a record's path

```text
Producer --metadata lookup--> broker cluster
Producer --key/partition routing--> partition leader --> follower replicas
Consumer group --assigned partitions--> fetch records --> business processing
Consumer --> commit next offsets to group coordination infrastructure
KRaft controller quorum --> manages cluster metadata/controller leadership
```

A broker stores partition logs; each partition has a leader and replica set. Controllers manage metadata and leadership, not every application record. KRaft is the modern metadata mode; historical ZooKeeper diagrams are not the architecture to assume for Kafka 4.x.

**Dig deeper:** distinguish replication factor from partition count. A three-replica partition has one logical ordered log, not three independent throughput partitions. What fails when controllers lose quorum versus when a partition leader fails?

## 3. How do keys, partitions, and consumer groups affect scaling?

| Decision | Benefit | Risk |
|---|---|---|
| Key by order/tenant | Related records generally route together | Hot key/tenant creates skew |
| More partitions | More storage/consumer parallelism | Metadata, rebalance, ordering migration, and per-partition overhead |
| More consumers in one classic group | Share partitions | Consumers beyond partition count are idle for that topic assignment |
| Separate groups | Independent processing/replay | Each group creates additional read/processing load |

Ordering is within a partition, not globally across a topic. The selected partitioner and partition count determine placement; adding partitions can move a key's future records to a different partition and affect continuity assumptions.

**Dig deeper:** can asynchronous processing of records from one partition reorder side effects? Yes—log order does not force completion order. How do you preserve ordering while scaling one very hot aggregate?

## 4. What do acknowledgements and replication actually guarantee?

Illustrative producer/topic configuration, not a complete deployment:

```properties
# producer
acks=all
enable.idempotence=true
# topic/broker policy, not a producer property
min.insync.replicas=2
# choose topic replication.factor=3 when creating it
```

`acks=all` waits for the required in-sync replica acknowledgement behavior; `min.insync.replicas` can reject writes when redundancy is insufficient. Availability and durability trade off during failures. Idempotent producer behavior addresses eligible producer retries, not every application-generated duplicate.

**Dig deeper:** a lost acknowledgement makes success ambiguous. What if an application restarts and sends the same business event as a new operation? What is the impact of unclean leader election? See [producer configuration](https://kafka.apache.org/41/configuration/producer-configs/).

## 5. At-most-once vs. at-least-once vs. exactly-once?

| Semantics | Typical sequence | Failure consequence |
|---|---|---|
| At-most-once | Advance progress before durable processing | Work can be lost |
| At-least-once | Process durably, then advance progress | Crash in between causes duplicates |
| Exactly-once within a defined boundary | Atomically coordinate result and progress | Scope matters; external effects need additional coordination |

Kafka transactions can atomically write Kafka outputs and consumer offsets for supported consume-transform-produce workflows; consumers must use suitable isolation such as `read_committed`. They do not automatically make a remote payment or arbitrary SQL transaction exactly-once.

**SQL consumer pattern:** in one DB transaction, insert a unique `(consumer_name,event_id)` receipt and apply the business update. Commit the Kafka offset afterward. On redelivery, an existing receipt means the DB effect has already been applied. The receipt and effect must commit together; use an external provider's idempotency support for external effects.

**Dig deeper:** what if deduplication receipts expire before a replay? What if producer sends two different event IDs for the same business operation?

## 6. What is an offset, and when should it be committed?

The committed offset convention identifies the **next** record to consume, not the last completed record. Disable automatic progress management when it conflicts with your processing boundary; choose behavior deliberately.

```text
poll partition P: offsets 10, 11, 12
process 10 successfully
process 11 fails; 12 may not safely advance progress past 11
safe committed next offset for P = 11
```

With parallel workers, maintain the contiguous completed prefix per partition. Committing past unfinished earlier records can skip work after a crash. Rebalances require careful ownership, cancellation/draining, and safe offset handling. [Consumer configuration](https://kafka.apache.org/41/configuration/consumer-configs/).

**Dig deeper:** a long task can exceed polling/ownership constraints. Does pausing a partition stop the need to maintain group protocol activity? What happens if an old worker finishes after its partition was reassigned?

## 7. How do retries and DLQs affect ordering?

| Policy | Benefit | Cost |
|---|---|---|
| Retry in place / pause partition | Preserve sequence | Head-of-line blocking |
| Retry topic / delayed queue | Main flow progresses | Later records can overtake failed one |
| DLQ after bounded attempts | Isolate poison data | Business event may remain unapplied; needs ownership and replay |
| Drop deliberately | Suitable only for explicitly disposable events | Permanent data loss |

Retry transient timeouts with a deadline, bounded attempts, exponential backoff, and jitter. Validation/schema errors generally need correction rather than endless retries. Preserve event ID, original topic/partition/offset, attempt count, failure category, and trace metadata in retry/DLQ envelopes; redact secrets.

**Dig deeper:** who watches the DLQ and how quickly? Replay must be authorized, rate-limited, observable, and idempotent. What if event B depends on failed event A?

## 8. What do you monitor and test?

Track consumer lag **and oldest unprocessed age**, partition skew, rebalance frequency, ISR changes, producer errors/latency, throughput, disk/retention headroom, and DLQ age. Lag alone can look healthy while consumers commit before performing side effects.

**Capacity example:** at 10 MB/s retained for one day, raw data is about 864 GB before replication, indexes, compression, and headroom. This is an estimate, not a sizing guarantee.

Test broker failure, slow DB, poison events, duplicate delivery, crash after DB commit, rebalance during processing, schema evolution, and full disks. Define compatibility rules for event schemas and stable event IDs from the start.

## References

- [Kafka design](https://kafka.apache.org/41/design/design/)
- [Producer configuration](https://kafka.apache.org/41/configuration/producer-configs/)
- [Consumer configuration](https://kafka.apache.org/41/configuration/consumer-configs/)
- [Kafka KRaft operations](https://kafka.apache.org/41/operations/kraft/)
- [Kafka delivery semantics](https://kafka.apache.org/41/design/design/#message-delivery-semantics)
