# Durable Workflows and Cloud Orchestration Cheat Sheet

[Study index](README.md) · Related: [distributed systems](Distributed_Systems.md), [infrastructure](Infrastructure_Automation.md), [background processing](Large_Data_Background_Processing.md).

A durable workflow records enough intent/progress to recover after process loss. A sequence of function calls plus logging is not automatically durable.

## Contents

- [1. How would you design environment provisioning?](#1-how-would-you-design-environment-provisioning)
- [2. What happens if resource creation succeeds but the response is lost?](#2-what-happens-if-resource-creation-succeeds-but-the-response-is-lost)
- [3. How do you prevent concurrent scaling, cloning, and upgrades from conflicting?](#3-how-do-you-prevent-concurrent-scaling-cloning-and-upgrades-from-conflicting)
- [4. Retry, timeout, compensation, or manual repair?](#4-retry-timeout-compensation-or-manual-repair)
- [5. How do cancellation, progress, and crash recovery work?](#5-how-do-cancellation-progress-and-crash-recovery-work)
- [6. How do workflow versions and timers survive deployments?](#6-how-do-workflow-versions-and-timers-survive-deployments)
- [7. How do you secure, observe, and test orchestration?](#7-how-do-you-secure-observe-and-test-orchestration)
- [References](#references)

## 1. How would you design environment provisioning?

```text
POST operation -> validate tenant/quota -> persist intent + outbox -> return operation ID
Worker: reserve placement -> create network -> create storage -> launch compute
        -> configure secrets -> verify readiness -> mark READY
Reconciler: compare durable state with provider reality; repair/retry safely
```

Persist operation ID, tenant, requested configuration/version, stage, resource IDs, attempt/deadline, error category, ownership/version, and terminal result. Separate desired environment state from one attempt to reach it.

| Execution style | Benefit | Cost |
|---|---|---|
| Synchronous request | Simple for very short work | Timeouts/retries tied to user connection |
| Queue + state table | Familiar components and control | You own timers, recovery, versioning, and races |
| Durable workflow engine | Managed history/timers/retry coordination | Engine semantics, SDK constraints, deployment/versioning |
| Reconciliation controller | Repairs desired vs. actual state repeatedly | Requires idempotent observation/actions and stable ownership |

**Dig deeper:** what does 202 mean if publishing the task fails? Persist enqueue intent atomically using an outbox, then dispatch. What is the status API and cancellation contract?

## 2. What happens if resource creation succeeds but the response is lost?

The result is unknown. Persist a stable provider request/idempotency token where supported, then retry/query using that identity. Otherwise search/reconcile by controlled ownership metadata and account for provider consistency before deciding whether to create again.

```text
Persist step intent (operation e42, step create-volume, key e42-volume-v1)
Call provider with same supported request key on retries
Persist returned volume ID and confirmed outcome
# Crash at any arrow must be recoverable by operation identity/provider observation.
```

A random new token on every retry defeats provider idempotency. Tags alone may not provide an atomic uniqueness guarantee; document the gap if the provider lacks a suitable primitive.

**Dig deeper:** how do you detect an orphan resource? What if listing is delayed? Who may delete it, and how do you prove ownership rather than matching a friendly name?

## 3. How do you prevent concurrent scaling, cloning, and upgrades from conflicting?

Define allowed transitions and per-environment operation compatibility. Use database versions/atomic claims or suitable fenced coordination. A lease should not let an expired worker continue overwriting a new operation.

```sql
UPDATE environments
SET state = 'UPGRADING', version = version + 1
WHERE id = :id AND tenant_id = :tenant
  AND state = 'READY' AND version = :expected_version
RETURNING version;
-- No returned row: reload and resolve conflict; do not continue blindly.
```

This guards a DB transition; external operations still need stable identity/version-aware handling. Record who owns the active operation and make recovery safe if ownership changes.

**Dig deeper:** can read-only inspection run during an upgrade? Can scale-in delete a node used by cloning? How do you express mutually exclusive vs. compatible operations?

## 4. Retry, timeout, compensation, or manual repair?

| Failure | Response | Reason |
|---|---|---|
| Temporary provider rate limit | Bounded backoff/jitter respecting provider signals | Avoid synchronized overload |
| Invalid configuration | Fail with actionable reason | Retry won't repair input |
| Ambiguous successful create | Query/reconcile stable operation | Prevent duplicate resources |
| Later step fails | Retry or compensating cleanup per policy | Earlier side effects already exist |
| Compensation fails | Persist repair-needed state and alert owner | Failure must not disappear into a log |

Deadlines exist per attempt, stage, and overall workflow. A long-running database upgrade cannot be “rolled back” merely by marking a row FAILED. Compensation may need a snapshot restore, rollback-compatible software, or operator intervention.

**Dig deeper:** do cleanup retries accidentally delete a resource now adopted by another operation? What is the retention/cost policy for a failed environment awaiting investigation? [Workflow error handling example](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html).

## 5. How do cancellation, progress, and crash recovery work?

Cancellation is usually a durable request checked at safe boundaries, not a guarantee that a remote action stops immediately. Model `CANCEL_REQUESTED`, `COMPENSATING`, and terminal outcomes deliberately. Some operations cannot safely stop mid-stage.

Recovery worker scans or receives timers for stale operations, observes actual resources, acquires authority, and advances/reconciles with version checks. Heartbeats show activity but not proof of correctness; a slow task may still be making progress.

**Dig deeper:** how do you distinguish a worker crash from a long provider call? Can recovery run twice? What counts as 50% progress when one stage takes most of the time?

## 6. How do workflow versions and timers survive deployments?

Pin an operation to a workflow/schema version or use an engine's supported versioning strategy. New code must understand in-flight history/state or deliberately migrate it. Persist deadlines; don't rely on a sleeping application thread surviving a restart.

| Approach | Benefit | Cost |
|---|---|---|
| Continue old version until completion | Stable semantics | Keep compatible workers/code available |
| Backward-compatible step evolution | Simpler rollout | Constraints on changes/history |
| Explicit state migration | Retire old logic | Must verify every in-flight state and rollback path |

**Dig deeper:** deterministic-replay engines constrain what workflow code can do directly; external side effects belong in their supported activity mechanism. How is an upgrade deployed while thousands of operations are running?

## 7. How do you secure, observe, and test orchestration?

Separate requester identity, execution identity, and current authorization. Scope provider permissions and tenant metadata; protect secrets and snapshots. Record stage latency, stuck age, retries, resource leakage, compensation failures, and cost.

Test a crash before/after every external call and durable write; duplicate deliveries; stale workers; provider throttling; cancellation; and deploy with operations in every stage. Verify no unowned billable resources and no false READY states.

**Resume drill:** whiteboard one actual provisioning/clone/upgrade path. Explain external APIs, durable records, failure recovery, and the operations team experience. State which coordination/recovery mechanisms were yours vs. supplied by the platform.

## References

- [AWS Step Functions error handling](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)
- [Kubernetes controller pattern](https://kubernetes.io/docs/concepts/architecture/controller/)
- [AWS idempotent API design](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [Temporal workflow execution](https://docs.temporal.io/workflow-execution)
