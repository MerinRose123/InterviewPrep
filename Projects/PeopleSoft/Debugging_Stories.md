# PeopleSoft Cloud Manager: debugging and release stories

[Cloud Manager guide](Cloud_Manager.md) · [Technology comparisons](../../Cheatsheets/Technology_Comparisons.md) · [Interview Q&A](05_Interview_QA.md)

## 1. Cloud Manager 16: OCI CLI dependency installation failure

### Confirmed facts

- The problem occurred during the **Cloud Manager 16 release**.
- Installation failed on release day despite an **exact OCI CLI version** being specified.
- A related OCI CLI dependency had an issue associated with its newer release.
- The fix was **prepackaging OCI CLI with its related dependencies** to address such installation issues in production.
- The dependency name, package versions, exact exception, affected-environment count, and recovery duration are not currently recalled.

These facts come from your account. Do not fill the missing details with a plausible package name or invented stack trace.

### A concise interview answer

“During the Cloud Manager 16 release, an OCI CLI dependency issue caused installation to fail on release day. We had already pinned the exact CLI version, but that alone did not make the installation reproducible: a newer release of a related dependency introduced a problem.

“We resolved it by prepackaging OCI CLI together with its dependencies, so the deployment used the packaged dependency set. The lesson was to control the complete dependency set rather than rely only on a top-level version pin. I do not recall the exact dependency or version, but I can explain the failure category and the packaging change we made.”

This preserves your confirmed facts. Describe your individual coding/debugging actions precisely if asked; the current account does not establish every investigation step or whether you alone implemented the fix.

### STAR structure

| Part | Your story |
|---|---|
| Situation | CM 16 release-day installation failure involving OCI CLI |
| Task | Restore reliable deployment and address dependency-related production installation failures |
| Action | Prepackage the CLI together with related dependencies |
| Result | The reported issue was resolved through the packaging change; no numerical reliability improvement is established |
| Learning | Pinning a top-level tool is different from controlling its full dependency set and installation inputs |

### Why an exact CLI pin can still be insufficient

**General mechanism:** a package can specify acceptable ranges for its dependencies. Selecting one CLI version does not necessarily select exactly one version of every transitive dependency. Different resolution times can produce different valid dependency selections; a newly released dependency can introduce an incompatibility or defect. Availability, Python version, OS/architecture and build tooling are additional installation inputs.

This explains the class of failure, but the exact dependency constraint and resolver output in your incident remain unverified. [pip repeatable-install guidance](https://pip.pypa.io/en/latest/topics/repeatable-installs/)

### Before and after

```text
Before — conceptual problem:
Deployment installs a fixed OCI CLI version
    → related dependency selection still depends on installation inputs
    → newer dependency release causes installation failure

After — confirmed remedy at a conceptual level:
Package OCI CLI together with its dependencies
    → distribute the packaged dependency set
    → use that set during deployment
```

The bundle format and exact installer flags are not recalled. Do not label it a Docker image, wheelhouse, fully offline installer, or hermetic build unless you confirm those details.

### Follow-up questions and defensible answers

**Why did pinning not prevent this?** “The CLI version was fixed, but pinning it did not fully fix the related dependency set. The incident involved a newer dependency release.”

**How did prepackaging help?** “It let us distribute the CLI with its dependencies as a controlled set instead of relying on the same installation-time dependency selection.”

**Which dependency failed?** “I do not recall the package name or exact version. It happened during CM 16. I would verify the release logs or fix before naming it.”

**Why not only pin that dependency?** “That could address the immediate version issue. Packaging the related dependency set addressed a wider reproducibility concern. The actual implementation was prepackaging; the complete set of alternatives discussed at the time is not recalled.”

**What was your personal contribution?** State whether you reproduced the failure, traced the dependency, changed packaging, changed installation, tested the artifact, or coordinated release validation. Only the remedy and incident context have been supplied so far.

**Was this an OCI service outage?** The confirmed issue was an OCI CLI-related dependency installation failure. Do not describe it as an OCI Compute/API outage without evidence.

**Did this eliminate all dependency problems?** “No universal guarantee follows from packaging. It controlled the bundled versions; runtime compatibility, artifact integrity and future security updates still needed management.”

### Validation to explain if you remember it

Retrieve the actual checks: clean-machine installation, supported OS/Python combinations, installing the artifact without unintentionally fetching newer dependencies, `oci --version`, and representative CLI execution. These are useful questions, not confirmed tests you performed.

Oracle documents manual/offline CLI installation and recommends an isolated environment rather than system-wide Python installation. That supports the broader packaging/isolation discussion; it does not establish your bundle format. [OCI CLI installation](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/climanualinst.htm)

### Improvements to discuss as proposals

- Record the resolved direct/transitive versions and supported target platforms with each artifact.
- Validate the packaged installation in clean release-like environments.
- Protect package integrity with appropriate hashes/signatures and trusted artifact distribution.
- Rebuild and retest bundles for security fixes rather than leaving them frozen indefinitely.

These are proposed engineering practices, not established features of your historical fix. Hash checking can verify that the installed bytes match expected package artifacts, but it does not prove the package is free of defects. [pip secure-install guidance](https://pip.pypa.io/en/stable/topics/secure-installs/)

## 2. Second debugging story: information still needed

One real incident has been supplied. Choose another issue you personally investigated, such as an add-node failure, credential update problem, Exadata integration bug, or deployment/runtime migration issue—but only if it actually happened.

For that incident, record: user-visible symptom, expected versus actual behavior, affected boundary, evidence inspected, hypotheses rejected, root cause, fix, validation and your individual contribution. Hypothetical failure exercises in the other guides are practice scenarios, not substitutes for a real incident.
