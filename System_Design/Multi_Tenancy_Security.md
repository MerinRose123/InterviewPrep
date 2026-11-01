# Multi-Tenancy and Platform Security Interview Cheat Sheet

[Study index](README.md) · Related: [authentication](Authentication_Authorization.md), [secrets](Cryptography_Passwords_Secrets.md), [Kubernetes](../Cheatsheets/Kubernetes.md).

Tenant isolation is an invariant across every storage and execution boundary, not just a WHERE clause in one controller.

## Contents

- [1. Shared tables vs. schemas vs. databases?](#1-shared-tables-vs-schemas-vs-databases)
- [2. How do you enforce tenant context?](#2-how-do-you-enforce-tenant-context)
- [3. How do you stop a noisy neighbor?](#3-how-do-you-stop-a-noisy-neighbor)
- [4. How should secrets and IAM be designed?](#4-how-should-secrets-and-iam-be-designed)
- [5. Network isolation, SSRF, supply chain, and Kubernetes security?](#5-network-isolation-ssrf-supply-chain-and-kubernetes-security)
- [6. How do cloning, export, deletion, and recovery affect isolation?](#6-how-do-cloning-export-deletion-and-recovery-affect-isolation)
- [7. How do you test and audit it?](#7-how-do-you-test-and-audit-it)
- [References](#references)

## 1. Shared tables vs. schemas vs. databases?

| Model | Advantage | Cost / risk |
|---|---|---|
| Shared tables with tenant key | Efficient provisioning and pooling | Every query/key/path needs isolation; restore and hot tenants harder |
| Schema per tenant | Logical separation/customization | Migration/catalog/pool management grows |
| Database per tenant | Stronger operational boundary, targeted backup | Fleet management and cost; cross-tenant analytics harder |
| Dedicated stack/account | Strong isolation for selected customers | Highest provisioning/operations cost |
| Hybrid tiers | Match isolation to requirements | Placement/routing and tier migration complexity |

**Scenario:** small tenants share infrastructure; a very large regulated customer receives dedicated resources. Define tenant-placement metadata and a controlled move procedure before promising seamless migration.

**Dig deeper:** tenancy, sharding, and replication solve different problems. Does database-per-tenant mean separate server? What are your data-residency and tenant-specific restore requirements?

## 2. How do you enforce tenant context?

Derive tenant access from verified identity and server-side membership; validate any requested tenant selection. Do not trust a free-form `X-Tenant-ID` from the internet as authorization.

```python
def load_export(principal, export_id):
    return Export.objects.get(id=export_id, tenant_id=principal.tenant_id)

cache_key = f"export:v2:{tenant_id}:{export_id}"
# Persist tenant_id on queued work and re-establish verified context in each worker.
```

Apply isolation to DB queries/joins, cache keys, object storage access, search filters, queue payloads, metrics/log access, and support tools. DB row-level security can be defense in depth, but connection/session role handling and privileged bypasses must be understood.

**Dig deeper:** pooled connections must not leak a previous tenant's context. What happens when a worker handles tenant A then B? Why do tests need two tenants with deliberately similar IDs/data?

## 3. How do you stop a noisy neighbor?

| Control | Protects | Tradeoff |
|---|---|---|
| Per-tenant rate limit | Admission rate | Bursts and global identity policy |
| Per-tenant concurrency cap | In-flight scarce resources | Fair queueing and starvation policy |
| Work-class queues/pools | Interactive traffic from bulk jobs | Idle capacity and operational overhead |
| Storage/size quotas | DB/object/log growth | Enforcement timing and customer experience |
| Dedicated placement | Extreme hot tenants | Cost and migration complexity |

Global FIFO can let one giant export starve small jobs. Use bounded work units, weighted fairness, tier quotas, and total global limits as appropriate. Track per-tier aggregates and use protected diagnostic data for individual tenants without unbounded metric labels.

**Dig deeper:** can a tenant open thousands of idle sockets or submit a huge compressed payload? Limit resource consumption, not only requests per minute.

## 4. How should secrets and IAM be designed?

Prefer workload identity/short-lived credentials and least privilege. Keep secrets out of source, images, URLs, logs, and plaintext state artifacts. Encrypt sensitive storage and restrict both KMS access and data access; “encrypted at rest” alone is not tenant authorization.

| Boundary | Practical control |
|---|---|
| Application to Vault | Scoped workload identity and audited access |
| App to DB | Narrow privileges; separate migration authority |
| CI/CD to cloud | Reviewed plans and short-lived deployment identity |
| Support/admin actions | Explicit elevated role, approvals where required, audit |
| Search/export access | Tenant/record policy before data leaves boundary |

**Dig deeper:** which services can rotate vs. read secrets? What is your cached-secret fallback during Vault outage? See [rotation and Shamir](Cryptography_Passwords_Secrets.md).

## 5. Network isolation, SSRF, supply chain, and Kubernetes security?

Use public/private network boundaries, constrained ingress/egress, authenticated internal calls, and network policy where the CNI supports enforcement. Private network placement does not replace authorization.

**SSRF scenario:** a webhook tester or URL-fetching agent is tricked into contacting metadata/internal services. Validate allowed targets and protocols; handle DNS resolution, redirects, alternate address forms, and egress enforcement. A simple string-prefix test is insufficient.

Containers should avoid unnecessary privileges, root, host mounts, and broad service accounts. Kubernetes Secret base64 is encoding, not encryption; configure appropriate encryption/access controls or external secret integration. Verify image provenance/dependency policy and protect CI credentials.

**Dig deeper:** namespace isolation alone is not a strong hostile-tenant boundary. What permissions can a compromised Pod use? How do you stop an agent from exfiltrating a secret through an allowed tool?

## 6. How do cloning, export, deletion, and recovery affect isolation?

Cloning production environments can copy credentials, personal data, and tenant identifiers. Sanitize data and regenerate environment-specific identities before exposing the clone. Retain provenance and tenant ownership for all artifacts.

| Operation | Question to answer |
|---|---|
| Export | Who can request/download it, and for how long? |
| Tenant deletion | What happens to caches, search, objects, backups, and pending jobs? |
| Restore one tenant | Can you recover it without overwriting others? |
| Placement migration | How do you fence writes and verify completeness? |
| Credential recovery | Are old revoked secrets accidentally reintroduced? |

Deletion from immutable backups may follow a retention/crypto-erasure policy rather than instantaneous physical removal; define requirements with stakeholders instead of making a blanket promise.

## 7. How do you test and audit it?

Test cross-tenant reads/writes, cache collisions, joins missing tenant predicates, direct object URLs, search queries, role changes during background execution, and privileged support endpoints. Audit actor, tenant, target, operation, decision, time, and trace/operation ID without recording secrets.

**Resume drill:** describe your actual tenancy model, how Django tests caught leakage, and how asynchronous context was propagated. Explain one isolation edge case and its verified fix; don't infer architecture solely from the term “multi-tenant.”

## References

- [Azure multitenant architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/overview)
- [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Kubernetes security checklist](https://kubernetes.io/docs/concepts/security/security-checklist/)
- [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
