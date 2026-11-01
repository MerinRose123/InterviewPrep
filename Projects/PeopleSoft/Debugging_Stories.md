# PeopleSoft Cloud Manager: debugging and release stories

[Cloud Manager](Cloud_Manager.md) · [Interview Q&A](05_Interview_QA.md) · [Details to recall](../README.md#details-to-recall)

## 1. Cloud Manager 16: OCI CLI dependency installation failure

### Interview answer

“During the Cloud Manager 16 release, installation failed despite pinning the exact OCI CLI version. A newer release of a related dependency caused the issue. We resolved it by prepackaging the CLI with its dependencies, so deployment used a controlled dependency set. The lesson was that pinning a top-level tool does not make its transitive dependencies reproducible.”

**Known scope:** release-day failure and the packaging remedy are confirmed. The dependency name/version, exception, affected-environment count, recovery time, bundle format, and Merin's individual investigation steps are not recorded. No numerical reliability improvement is established.

### Failure mechanism

A package can allow a range of dependency versions. Pinning the CLI alone may therefore resolve different transitive versions on different installation dates. Python/OS compatibility, artifact availability, and build tooling are additional inputs. The exact historical resolver output is unavailable. See [pip repeatable installations](https://pip.pypa.io/en/latest/topics/repeatable-installs/).

### Follow-up questions

- **Why prepackage rather than pin one dependency?** A narrow pin could fix an immediate incompatibility; distributing a tested set addresses broader reproducibility. The full alternatives considered historically are not recorded.
- **What did packaging change?** It controlled the distributed dependency set. It does not establish a Docker image, wheelhouse, or fully offline installer.
- **How would you validate it?** Test clean release-like environments and supported OS/Python versions, verify the intended CLI/dependency versions, and exercise representative operations. These are proposed checks, not confirmed historical tests.
- **What is the maintenance cost?** Rebuild and validate for security fixes and runtime changes; verify artifact integrity. A frozen dependency set is not permanently safe or compatible.

Oracle documents [manual/offline CLI installation](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/climanualinst.htm); pip documents [secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/). Neither source establishes the historical bundle format.
