# Infrastructure Automation Interview Cheat Sheet

[Study index](README.md) · Related: [Kubernetes](../Cheatsheets/Kubernetes.md), [workflows](Workflow_Orchestration.md), [security](Multi_Tenancy_Security.md).

This guide owns tool ownership, delivery stages, images, cleanup, and operational cost. State, locking, plans, drift, modules, and partial-apply recovery are explained once in [Terraform](../Cheatsheets/Terraform.md).

## Contents

- [1. Declarative IaC vs. configuration management vs. images?](Infrastructure_Automation.md#declarative-iac-vs-configuration-management-vs-images)
- [Delivery boundaries and recovery](#delivery-boundaries-and-recovery)
- [6. Design a safe CI/CD pipeline](Infrastructure_Automation.md#design-a-safe-cicd-pipeline)
- [7. Images, patching, cleanup, and cost?](Infrastructure_Automation.md#images-patching-cleanup-and-cost)
- [References](#references)

## Declarative IaC vs. configuration management vs. images?

| Tool/style | Fit | Tradeoff |
|---|---|---|
| Terraform/OpenTofu | Provision cloud resource graph | State, provider semantics, partial applies |
| Puppet/configuration management | Converge machine configuration | Agent/ordering/drift and mutable host lifecycle |
| Packer/image baking | Versioned machine images | Rebuild/promotion pipeline and image sprawl |
| Shell/Python imperative automation | Integrate missing lifecycle operations | You own idempotency, retries, state, and recovery |

**Scenario:** bake dependencies into an image, provision compute/network through IaC, and use a controlled boot/configuration phase for environment-specific settings. Avoid multiple tools independently owning the same mutable property.

**Dig deeper:** “declarative” does not mean safe or transactional. Which changes replace a resource? What is the source of truth when someone makes an emergency manual change?


## Delivery boundaries and recovery

An image build, infrastructure run, configuration step, schema migration, and application rollout have different owners and success criteria. Record artifact versions, environment/operation identity, readiness evidence, and recovery responsibility across these stages. Avoid two tools managing the same mutable property.

If a stage fails, preserve its evidence and inspect the actual outcome before retrying. Reverting application code does not automatically reverse a schema migration or recover deleted data. Use the [workflow guide](Workflow_Orchestration.md) for durable cross-stage recovery and the [Terraform guide](../Cheatsheets/Terraform.md#8-failures-drift-import-and-recovery) for provider/state failures.

## Design a safe CI/CD pipeline

```text
Change -> format/validate/unit checks -> security/policy checks -> plan
       -> review -> apply exact reviewed artifact with scoped identity
       -> smoke/health verification -> staged traffic/rollout -> monitor
```

Protect production credentials and plan artifacts, isolate untrusted PR execution, and use short-lived cloud identities where supported. Serialize conflicting deployments and retain audit/approval evidence appropriate to the environment. Separate schema migration compatibility from application rollout.

**Dig deeper:** can a PR execute arbitrary provider/module code with production credentials? What happens if artifact contents change between approval and apply? A successful Jenkins job is not proof the service is healthy.

## Images, patching, cleanup, and cost?

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

- [Packer documentation](https://developer.hashicorp.com/packer/docs)
