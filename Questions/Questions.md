# Scenario-Based Interview Questions

Practice answering each prompt aloud, then compare your approach with the sample answer. Each scenario covers the decisions you’d make and how you’d verify the outcome.

## Backend APIs

### 1. Flask API versioning

> Your Flask API needs to support versioning to handle breaking changes while maintaining backward compatibility. How would you design and implement API versioning, and what factors would you consider in this scenario?

I’d start by identifying which clients use the API and what contracts they depend on, including response fields, status codes, and behavior. For a breaking change, I’d register separate Flask blueprints under `/api/v1` and `/api/v2`. If clients already use unversioned routes, I’d keep those routes mapped to the original contract. Each version would own its serializers and HTTP behavior, with shared business logic where the semantics match. URL versioning makes the version visible in requests, logs, and docs. Header versioning is another option if stable URLs matter, but the gateway and caches must distinguish versions.

I’d publish an OpenAPI spec and migration examples for each version, run contract tests against both, and track traffic and errors by version and client. I’d communicate a deprecation timeline and use observed adoption to decide when to retire v1. Compatible additions can stay in the same version if existing client contracts allow them.

[Flask blueprint documentation](https://flask.palletsprojects.com/en/stable/blueprints/)

### 2. Django REST Framework error handling

> You inherit a Django REST API with inconsistent error responses across endpoints. How would you standardize error handling to ensure consistent and informative error messages for both clients and developers?

I’d inventory the current responses and define a common JSON shape with a stable error code, a client-facing message, a request ID, and optional field-level errors. In Django REST Framework, I’d configure a global `EXCEPTION_HANDLER` that calls DRF’s default handler first, then normalizes the body while preserving HTTP status and headers. I’d route validation through `serializer.is_valid(raise_exception=True)`, update views that return error responses directly, and cover API routing errors and unexpected failures with JSON fallbacks.

For a 500, I’d return a generic message and log the exception internally with the same request ID and redacted context. I’d document the schema and test representative validation, authentication, permission, missing-resource, throttling, and server-error cases. If clients parse existing error bodies, I’d coordinate the rollout as a contract change.

[DRF exception handling documentation](https://www.django-rest-framework.org/api-guide/exceptions/)

## Data and SQL

### 3. Data model and reporting performance

> You join a project where the current data model causes slow report generation and frequent schema changes. What steps would you take to assess and optimize the data model?

I’d pick representative slow reports, establish latency and freshness targets, and trace their SQL using representative data. I’d inspect execution plans and row counts for scans, expensive joins, sorts, and poor estimates. In parallel, I’d review recent schema changes and ask which business concepts keep changing. That helps distinguish a query problem from a model that no longer matches how the business uses the data.

I’d start with measured changes such as query rewrites or indexes that match common joins and filters, checking their write and storage costs. If reports repeatedly aggregate large transactional tables, I’d evaluate a reporting table or materialized view with an explicit refresh and freshness target. I’d stage any schema change with an additive migration, a batched backfill, and a controlled read cutover. I’d compare report totals, latency, write performance, and refresh lag before retiring the old path.

### 4. SQL job recovery after a migration

> A business-critical SQL job failed due to unexpected NULL values after a recent data migration. As the lead, how would you investigate and resolve this issue while minimizing downtime?

I’d stop automated retries if the job can produce duplicate or partial results, identify the last successful run, and confirm the downstream impact. I’d trace the failing rows back to the migration and compare source and target data, column defaults, join coverage, and load order. I’d confirm what NULL means for that field before choosing a fix.

If the correct values can be recovered, I’d repair the affected rows in batches and reconcile counts and totals before resuming from a known checkpoint. I’d check for partial writes and make the replay idempotent. If a repair takes longer than the recovery window, I’d evaluate using the last verified snapshot and account for newer writes before switching. After recovery, I’d correct the migration and add preflight checks and monitoring. I’d add a database constraint only if the business rule genuinely requires a value.

## Python integration and migration

### 5. Third-party API handling sensitive data

> You’re tasked with integrating a third-party API into an existing Python workflow that handles sensitive user data. What key considerations and steps would you take to ensure secure and reliable integration?

I’d map what data leaves the workflow, confirm what the provider needs, and review retention, deletion, subprocessors, and incident notification with the relevant owners. I’d send the smallest payload possible, use TLS and scoped credentials stored in a secrets manager, and redact sensitive fields from logs and traces. I’d validate incoming responses and use synthetic data in tests.

I’d put the integration behind a dedicated client with connection and read timeouts, rate-limit handling, and bounded backoff with jitter for transient failures. For writes, I’d retry only when the operation is idempotent or the provider supports an idempotency key. I’d define how the workflow behaves during an outage, such as durably queuing eligible requests for replay, and monitor latency, error rates, and backlog. I’d roll out gradually and verify recovery from timeouts and partial failures.

### 6. Python 2 to Python 3 migration

> You’re asked to migrate a Python 2-based batch processing system to Python 3 while ensuring minimal downtime. Briefly outline your migration strategy, highlighting tools and risk mitigation steps.

I’d inventory jobs, dependencies, schedules, and output contracts, then select a supported Python 3 runtime and replace incompatible packages. I’d use static checks and dependency review to guide the port, with `pytest` fixtures covering text versus bytes, integer division, date handling, serialization, and database drivers. I’d capture representative Python 2 outputs and compare them against Python 3 results using the same inputs.

I’d run Python 3 in shadow mode with isolated outputs, compare results, runtimes, and resource use, then switch a small set of jobs at a scheduler boundary. At cutover I’d ensure only one version publishes results, verify checkpoints, and keep the previous runner available for a short rollback window. I’d rehearse resuming from the last verified checkpoint so a rollback doesn’t duplicate writes.

## AWS and fraud detection

### 7. EC2 cost optimization

> A client wants to reduce AWS costs for a fleet of EC2 instances with variable workloads. What AWS features and strategies would you use to optimize cost without sacrificing performance or reliability?

I’d establish baseline cost, peak demand, and latency and availability targets. I’d use CloudWatch metrics and Compute Optimizer recommendations to identify downsizing candidates, then load-test them. I’d use a multi-AZ Auto Scaling group and scale on a metric that tracks demand, such as requests per target for a web service or backlog per worker for a queue.

I’d keep enough On-Demand capacity for critical traffic and use diversified Spot capacity for interruption-tolerant workers that can drain or resume jobs. Capacity Rebalancing can help replace at-risk Spot instances. After right-sizing and scaling, I’d consider Savings Plans for the stable usage floor. I’d track cost per request or job alongside tail latency, errors, and queue age to verify the savings.

[AWS Compute Optimizer](https://docs.aws.amazon.com/compute-optimizer/latest/ug/savings-estimation-mode.html) · [EC2 purchasing options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html) · [EC2 Capacity Rebalancing](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-capacity-rebalancing.html)

### 8. Real-time fraud detection

> A financial services firm wants to deploy Agentic Ai for real-time fraud detection. What steps would you take to ensure the system adapts to evolving fraud patterns while minimizing false positives?

I’d keep the real-time decision path bounded by a latency budget and use rules and a calibrated risk model to score transactions. I’d use separate thresholds for approving, requesting extra verification, routing to review, and declining. The agent could gather approved evidence and summarize it for investigators. Any action it can take would be limited by explicit policy, with an audit trail and a fallback to known rules if the model or agent is unavailable.

I’d collect investigator outcomes and confirmed fraud labels, accounting for delayed chargebacks and the limited feedback on declined transactions. I’d monitor precision, recall, legitimate declines, review volume, and fraud loss by segment, alongside feature drift and response latency. I’d evaluate proposed changes on time-separated data and use shadow or canary deployment before promotion. Thresholds should reflect the cost of missed fraud, the impact on legitimate customers, and available review capacity. I’d version rules and models so the team can roll back quickly.
