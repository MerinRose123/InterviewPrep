# PeopleSoft — Engineering challenges

[Project guide](Cloud_Manager.md) · [Architecture](Runtime_Architecture.md) · [Terraform](../../Cheatsheets/Terraform.md) · [Debugging stories](Debugging_Stories.md)

## Interview opening (90 seconds)

“I worked on PeopleSoft Cloud Manager, a platform for provisioning and managing PeopleSoft environments on OCI. My backend and infrastructure work spanned Python, Java, REST integrations, Terraform/OpenTofu, Jenkins, OCI services, and lifecycle operations such as cloning, scaling, upgrades, and image creation. I contributed to OCI Vault-based credential management, OpenSearch cluster support, Exadata integration, and CI/CD automation. The engineering challenges were coordinating long-running infrastructure operations, recovering from partial failures, managing credentials across changing environments, and making deployment repeatable.”

## Challenge: a cloud operation succeeds after the API call times out

**Interviewer:** “You call OCI to create a VM, the request times out, and your orchestration job retries. How do you avoid creating two VMs?”

**System boundary:** Cloud Manager's job state and OCI's actual resource state are not a single transaction.

**Reasoning:** A timeout means the caller did not receive a result; it does not mean OCI did not create the resource. Treat the outcome as unknown. Associate the workflow with a stable operation identity and record provider request/resource identifiers. On recovery, query the provider's operation and resource state before deciding whether to retry. Make subsequent configuration steps repeatable where possible. Cleanup must distinguish resources created by the operation from imported or shared resources.

**Trade-offs:** Blind retry is simple but risks duplication and cost. Always rolling back can delete useful partial work. Reconciliation adds complexity but makes long-running cloud operations safer.

**Follow-ups:** What if two workers resume the same job? How do you prevent stale workers from modifying a newer environment? What if a VM exists but bootstrap failed? Which steps can be repeated safely?

**Whiteboard exercise:** Draw job record → OCI create → delayed result → reconciliation → bootstrap → readiness check. Show a crash at each boundary.

## Challenge: provisioning partially completes

**Interviewer:** “The VM is running, but the PeopleSoft domain or database configuration fails. What is your recovery strategy?”

Separate infrastructure readiness, software deployment, database connectivity, and application readiness. Store progress at meaningful phase boundaries; preserve logs and operation IDs. Retry only recoverable steps, and define compensation for owned temporary resources. Some changes, particularly database and application upgrades, are better handled by restore or forward repair than by naïvely reversing commands.

**Trade-off:** Fine-grained checkpoints improve recovery but increase orchestration state and testing requirements. A single success flag is simpler but conceals partial success.

**Follow-ups:** How would you implement retry backoff? What is your maximum retry policy? How do you avoid concurrent clone/patch operations? What would you alert on?

## Challenge: OCI Vault credential rotation during scaling

**Project contribution:** OCI Vault-based centralized credential management, including rotation, recovery, and scaling-related updates, with approximately 15 engineering hours saved monthly as described in the project materials.

**Interviewer:** “A password rotates while an additional node is being created. One consumer still has the old password. What happens?”

Explain the authority for the current credential, the consumers that need it, the update sequence, and the point at which a new credential becomes active. Credential rotation is a distributed coordination problem: changing the secret value and updating every dependent process are separate actions. A scaling workflow should fetch or validate the credential generation it needs, rather than assume a cached password remains valid. Handle failed consumer updates explicitly and validate fresh connections after rotation.

**Alternatives:** A shared secret with coordinated rollout is operationally different from short-lived identities or per-service credentials. OCI Vault stores and controls secret access; it does not by itself guarantee atomic propagation to every running application.

**Follow-ups:** Difference between rotating a Vault encryption key and changing a database password? What if one node is offline? How do IAM policies limit blast radius? How would you audit access without logging secrets?

## Challenge: OpenSearch node expansion and reindexing

**Project contribution:** Search cluster integration and add-node functionality.

**Interviewer:** “You added a new OpenSearch node. Do you need to reindex everything?”

Not necessarily. Cluster expansion and reindexing solve different problems. A compatible new data node can receive existing shards through allocation and rebalancing. Reindexing rebuilds searchable documents and may be needed for index mapping or data changes, not merely because capacity increased.

**Walkthrough:** Check node compatibility and discovery → join cluster → inspect cluster health and shard allocation → observe relocation and capacity → validate query and indexing behavior. Distinguish primary/replica shard movement from rebuilding source data.

**Trade-offs:** More nodes add capacity and availability options but also network, coordination, and operational overhead. Replicas improve availability but increase storage and write work. A cluster can be green while business search results are stale.

**Follow-ups:** What if a node never joins? What if shards stay unassigned? How do you avoid overloading the cluster during rebalancing? How do you validate search freshness?

## Challenge: Exadata integration across lifecycle operations

**Project contribution:** Exadata convergence and lifecycle integration.

**Interviewer:** “How does an Exadata-backed environment change cloning or scaling compared with a database on a VM?”

Separate the application topology from database service placement. Cloud Manager must coordinate compatible connectivity, service discovery, database lifecycle capabilities, authentication, and validation. Exadata, RAC, database instances, and pluggable databases are distinct concepts. A clone can involve application configuration and database-specific work; scaling an application node does not imply scaling the database the same way.

**Trade-offs:** Specialized database infrastructure provides operational and performance capabilities but creates more integration paths, compatibility constraints, and failure modes.

**Follow-ups:** What does RAC provide that sharding does not? How would you detect a service-name or network configuration error? Which checks show application-level readiness?

## Real incident: Cloud Manager 16 OCI CLI dependency failure

**Situation:** Installation failed during the Cloud Manager 16 release despite an exact OCI CLI version being specified. A newer related dependency caused an installation issue.

**Resolution:** Package the OCI CLI together with its dependencies to control the installed dependency set.

**Engineering lesson:** Pinning the top-level tool is not the same as pinning the complete dependency graph. Reproducible deployment requires control of transitive dependencies and the installation artifact.

**Interviewer follow-ups:** Why did the version pin fail? Why package rather than pin only one dependency? How would you test the artifact on a clean release-like environment? How would you handle security updates to the packaged dependencies?

## Challenge: Terraform/OpenTofu state and conflicting operations

**Interviewer:** “Two deployment jobs apply changes to the same environment. What can go wrong?”

State is a record of managed infrastructure, not a lock on every external workflow. Concurrent applies can conflict; state locking and serialized environment operations protect different layers. Plan/apply separation, provider compatibility, drift inspection, secret handling, and safe import/migration all matter.

**Trade-offs:** Splitting state reduces contention and blast radius but complicates dependencies. One large state simplifies cross-resource references but makes locking and recovery more consequential.

**Follow-ups:** How do you recover after an apply is interrupted? What is drift? What happens if a resource exists in OCI but not in state? How do you migrate Terraform to OpenTofu safely?

## Challenge: Jenkins automation, cleanup, and cost

**Project contribution:** Jenkins pipeline and cleanup improvements, including a reported 25% cloud cost reduction from resource cleanup automation.

**Interviewer:** “How do you safely delete unused test environments?”

Define resource ownership, age, dependencies, exclusions, and deletion eligibility. Separate discovery from deletion; make cleanup repeatable and auditable. Avoid deleting imported, shared, or active resources. Validate that a cleanup job cannot race with a provisioning job.

**Trade-offs:** Aggressive cleanup reduces spend but risks disrupting engineering work; conservative cleanup costs more. Use tagging, approvals for risky cases, and dry runs when appropriate.

## Rapid-fire interview scenarios

| Question | Core engineering answer |
|---|---|
| Provisioning job says success, application is unavailable | Separate API completion, VM state, service health, database connectivity, and application readiness |
| Two operators trigger clone and patch | Serialize incompatible environment mutations; enforce operation ownership |
| Lost asynchronous callback | Reconcile against durable job/provider state; do not assume failure |
| Credential update succeeds on only some nodes | Coordinate consumer updates, detect mixed generations, validate new connections |
| Search cluster green but data missing | Check indexing pipeline, index aliases, refresh, access control, and query semantics |
| New OpenSearch node adds no capacity | Inspect roles, shard allocation, disk watermarks, and placement constraints |
| Terraform plan changes unexpected resources | Investigate drift, provider/version differences, state, and configuration |
| Release-day package installation fails | Inspect transitive dependencies and artifact reproducibility |
| High customer adoption but unknown throughput | Discuss workload-specific concurrency, latency, operation durations, and bottlenecks |
