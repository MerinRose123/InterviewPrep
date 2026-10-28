# Infrastructure Automation Interview Cheat Sheet

[Study index](README.md) · Related: [cloud](Cloud_Kubernetes_CheatSheet.md), [workflows](Workflow_Orchestration_CheatSheet.md), [security](Multi_Tenancy_Security_CheatSheet.md).

Terraform examples explain a review process; they are not commands executed by this guide. OpenTofu has related concepts but its versions/backends/features must be checked independently.

## Contents

- [1. Declarative IaC vs. configuration management vs. images?](#1-declarative-iac-vs-configuration-management-vs-images)
- [2. What is Terraform state, and why lock it?](#2-what-is-terraform-state-and-why-lock-it)
- [3. Plan vs. apply vs. drift detection?](#3-plan-vs-apply-vs-drift-detection)
- [4. Why can an apply partially succeed?](#4-why-can-an-apply-partially-succeed)
- [5. How do you structure state and modules?](#5-how-do-you-structure-state-and-modules)
- [6. Design a safe CI/CD pipeline](#6-design-a-safe-cicd-pipeline)
- [7. Images, patching, cleanup, and cost?](#7-images-patching-cleanup-and-cost)
- [References](#references)

## 1. Declarative IaC vs. configuration management vs. images?

| Tool/style | Fit | Tradeoff |
|---|---|---|
| Terraform/OpenTofu | Provision cloud resource graph | State, provider semantics, partial applies |
| Puppet/configuration management | Converge machine configuration | Agent/ordering/drift and mutable host lifecycle |
| Packer/image baking | Versioned machine images | Rebuild/promotion pipeline and image sprawl |
| Shell/Python imperative automation | Integrate missing lifecycle operations | You own idempotency, retries, state, and recovery |

**Scenario:** bake dependencies into an image, provision compute/network through IaC, and use a controlled boot/configuration phase for environment-specific settings. Avoid multiple tools independently owning the same mutable property.

**Dig deeper:** “declarative” does not mean safe or transactional. Which changes replace a resource? What is the source of truth when someone makes an emergency manual change?

## 2. What is Terraform state, and why lock it?

State maps configuration resource addresses to real resource identities and tracked metadata. Remote state can support collaboration and recovery; secure access, versioning, encryption, and backend-supported locking are operational requirements.

A state lock serializes supported operations for that state; it does not prevent manual cloud changes or two separate states managing the same resource. Do not disable locking to make a blocked pipeline “work.” Force-unlock only after verifying the original operation is no longer active and following recovery policy. [State locking](https://developer.hashicorp.com/terraform/language/state/locking).

**Dig deeper:** what if an apply process crashes while a provider request is still running? Why can a different workspace/state still create conflicting resources? How do you prevent overly broad state access across tenants?

## 3. Plan vs. apply vs. drift detection?

```sh
terraform fmt -check
terraform init
terraform validate
terraform plan -out=reviewed.tfplan
terraform show reviewed.tfplan
# Apply only the reviewed artifact in an authorized deployment stage:
terraform apply reviewed.tfplan
```

A plan compares configuration, tracked state, and observed resources under provider behavior. It is not proof that a later apply cannot fail or that external conditions remain unchanged. Saved plans/state can contain sensitive information even when terminal output redacts it. [Plan semantics](https://developer.hashicorp.com/terraform/cli/commands/plan).

| Situation | Action to reason about |
|---|---|
| Expected config change | Review additions, updates, replacements, deletions, scope |
| Manual drift | Decide to codify, revert, or import under ownership |
| Stale reviewed plan | Regenerate/review rather than assuming unchanged reality |
| Provider upgrade | Pin/test versions and inspect diff semantics |

**Dig deeper:** validation checks configuration structure, not every cloud permission/quota. How are provider/module dependencies pinned and reviewed?

## 4. Why can an apply partially succeed?

Cloud APIs and resource operations are not one global ACID transaction. Some resources may exist when a later step fails. Preserve state/evidence, inspect provider reality, reconcile ownership, then retry or compensate. Blindly rerunning with new names can leak resources.

| Recovery | Benefit | Risk |
|---|---|---|
| Retry toward desired state | Reuses tracked successes | Provider/idempotency gaps remain |
| Revert configuration | May restore earlier desired state | Replacement/deletion can be destructive; not automatic rollback |
| Import/reconcile orphan | Recover tracking | Must verify identity and avoid dual ownership |
| Controlled cleanup | Remove failed-environment cost | Dependency order and tenant safety |

**Dig deeper:** reverting Git does not resurrect deleted data. Why is `-target` a special recovery tool rather than a normal permanent dependency strategy? How do you audit resource ownership before cleanup?

## 5. How do you structure state and modules?

Separate by lifecycle, failure blast radius, permissions, and deployment ownership—not merely by resource type. A single giant state centralizes risk; hundreds of tiny states create dependency/orchestration overhead.

```hcl
variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "environment must be dev, stage, or prod"
  }
}
```

Modules should expose meaningful inputs/outputs and stable contracts. Avoid copying every provider argument into an indistinguishable wrapper without simplifying ownership or policy. Sensitive outputs are not a guarantee the underlying value is absent from state.

**Dig deeper:** how do you move/rename a resource address without recreation using supported migration constructs? How do dependent states discover an endpoint without broad secret exposure?

## 6. Design a safe CI/CD pipeline

```text
Change -> format/validate/unit checks -> security/policy checks -> plan
       -> review -> apply exact reviewed artifact with scoped identity
       -> smoke/health verification -> staged traffic/rollout -> monitor
```

Protect production credentials and plan artifacts, isolate untrusted PR execution, and use short-lived cloud identities where supported. Serialize conflicting deployments and retain audit/approval evidence appropriate to the environment. Separate schema migration compatibility from application rollout.

**Dig deeper:** can a PR execute arbitrary provider/module code with production credentials? What happens if artifact contents change between approval and apply? A successful Jenkins job is not proof the service is healthy.

## 7. Images, patching, cleanup, and cost?

Version images with provenance, scan and patch through controlled rebuilds, test startup/rollback, and retire old artifacts after their retention window. Use TTL/ownership metadata for temporary environments, but require safety checks before deleting resources with dependencies or customer data.

| Cost lever | Check before applying |
|---|---|
| Right-size compute | Actual load, headroom, burst and DR needs |
| Autoscale | Startup delay, quotas, minimum capacity, downstream limits |
| Cleanup | Ownership, exclusions, last activity, recoverability |
| Storage tiering | Retrieval latency/cost, access pattern, retention |
| Reduce repeated work | Cache/artifact reuse correctness and expiry |

**Resume drill:** explain the baseline behind your cloud-cost reduction, what changed, and how you checked reliability after cleanup/patching improvements. Use actual attribution and measurement, not a hypothetical percentage.

## References

- [Terraform state locking](https://developer.hashicorp.com/terraform/language/state/locking)
- [Terraform plan](https://developer.hashicorp.com/terraform/cli/commands/plan)
- [Terraform sensitive data](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)
- [OpenTofu state](https://opentofu.org/docs/language/state/)
- [Packer documentation](https://developer.hashicorp.com/packer/docs)
