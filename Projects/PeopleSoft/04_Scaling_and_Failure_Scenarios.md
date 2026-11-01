# PeopleSoft Cloud Manager — scaling and failure scenarios

[Architecture](02_Architecture_and_Data_Flow.md) · [Challenges](03_Engineering_Challenges.md) · [Interview drills](05_Interview_QA.md)

These are design exercises grounded in Cloud Manager's responsibilities. The contribution is real where documented; the proposed recovery mechanisms below do not establish the historical implementation. Cloud Manager did not use Celery or Kafka.

## Provisioning times out after OCI creates a resource

**Invariant:** one logical environment operation must not produce duplicate, untracked infrastructure.

**Walkthrough:** Persist an operation identity and owned resource references. A timeout leaves the outcome unknown; inspect OCI work/resource state before issuing another create. Resume from the observed phase and preserve diagnostics. Two recovery workers need coordinated ownership so a stale worker cannot overwrite newer status.

**Tradeoff:** Reconciliation is more complex than blind retries, but avoids duplicate resources and cost. Compensation must exclude imported/shared resources.

**Verify:** simulate a lost response and a worker restart. Check operation completion time, orphan-resource count, duplicate resource creation, and recovery attempts.

## Scale and upgrade target the same environment

**Invariant:** incompatible lifecycle changes must not mutate an environment concurrently.

**Walkthrough:** Define which operation pairs may overlap; serialize incompatible ones using durable environment-level ownership. Recheck ownership before committing a phase and reconcile after a worker dies. A Terraform state lock protects supported state operations, not every application workflow.

**Tradeoff:** Strict serialization simplifies correctness but limits concurrency; permit parallel work only when dependencies and writes are independent.

**Verify:** submit simultaneous operations and resume an old worker after ownership changes. Track queue wait, rejected/conflicting operations, and stale updates.

## A new search node joins but search remains unhealthy

**Invariant:** capacity expansion must preserve valid cluster membership and application-level search behavior.

**Walkthrough:** Separate VM/bootstrap readiness, discovery/security compatibility, node roles, shard allocation, and source-data freshness. Check disk watermarks and placement constraints before adding more nodes. Rebalancing shards and rebuilding an index are distinct operations.

**Tradeoff:** More nodes/replicas add headroom and availability options but increase recovery traffic, storage, and coordination.

**Verify:** test node loss and failed join; measure unassigned shards, relocation time, rejection rate, query latency, and indexing lag. A green cluster alone does not validate business results.

## Credential rotation overlaps with add-node

**Invariant:** a ready node must use the intended valid credential without leaving existing consumers stranded.

**Walkthrough:** Identify the credential authority, consumer set, activation sequence, and version a scaling job needs. Handle partial consumer updates and validate fresh connections. Do not log secrets. Recovery order depends on whether the backing service permits overlapping credentials.

**Tradeoff:** Coordinated rotation increases orchestration work; cached credentials reduce reads but create staleness risk.

**Verify:** fail one consumer update and bring an offline node back. Measure failed authentication, mixed credential generations, recovery time, and audit completeness.

## Cleanup races with an active deployment

**Invariant:** cleanup must delete only eligible resources owned by its target scope.

**Walkthrough:** Confirm ownership, current operation state, age/retention, exclusions, and dependency order immediately before deletion. Protect shared/imported resources and serialize conflicting environment changes. Preserve a record of what was removed.

**Verify:** test an environment that becomes active between discovery and deletion, partial deletion, and a retry. Compare resource retention and cloud cost without treating lower spending as proof of correct cleanup.

## Exadata clone reports success but the application cannot connect

**Walkthrough:** Check the database service endpoint, network/DNS resolution, listener/service configuration, credentials, client compatibility, and application domain configuration. Infrastructure and database-job completion are separate from a representative application query succeeding.

**Verify:** inject a bad endpoint or stale credential and ensure readiness does not declare success. Explain your actual integration module and validation separately from this proposed diagnostic sequence.

For each exercise, draw the failed boundary, authoritative state, safe retry condition, and one signal that proves recovery. Use the [confirmed release incident](Debugging_Stories.md) when asked what actually happened in production.
