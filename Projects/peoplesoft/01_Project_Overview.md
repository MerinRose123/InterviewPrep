# PeopleSoft Cloud Manager — project overview

## 2. Product and vocabulary

PeopleSoft Cloud Manager automates provisioning and lifecycle management of PeopleSoft environments on OCI. Think of an environment as a coordinated set of infrastructure, software installations, domains, configuration, database services, and operational metadata. An administrator describes the desired environment; Cloud Manager coordinates the steps needed to produce and maintain it. Oracle delivers the application through OCI Marketplace. [Oracle product overview](https://docs.oracle.com/en/applications/peoplesoft/cloud-manager/22/peoplesoft-cloud-manager-for-oracle-cloud-infrastructure/understanding-peoplesoft-cloud-manager-oracle-cloud-infrastructure.html)

Cloud Manager and the managed application have different responsibilities:

- **Cloud Manager:** provisioning, configuration, lifecycle jobs, administrative policies, resource inventory, and operational status.
- **Managed PeopleSoft environment:** business transactions, PeopleCode, application data, integrations, batch jobs, search, and reports.
- **OCI:** compute, networks, storage, IAM, database services, and other infrastructure capabilities used by these systems.

Cloud hosting does not turn PeopleSoft into Oracle Fusion Cloud Applications. Nor does Cloud Manager imply that all customers use one centrally operated SaaS instance. Describe the installation and tenancy model of the deployment you actually worked on.

| Term | Meaning | Interview distinction |
|---|---|---|
| PeopleSoft application | HCM, FSCM, Campus Solutions, etc. | Business product and data model |
| PeopleTools | Runtime and tooling underlying PeopleSoft | Its release affects middleware and search compatibility |
| Cloud Manager image | Release of Cloud Manager | Different version axis from PeopleTools and application update images |
| Topology | Nodes, VM properties, and component placement | Defines the infrastructure layout |
| Environment template | Reusable environment provisioning configuration | Selects content/topology and relevant settings |
| Environment | Provisioned or imported deployment | Running resources plus configuration and metadata |
| DPK | Deployment package | Software/configuration packaging, not a live VM |
| PUM | PeopleSoft Update Manager | Selective application maintenance; different from Cloud Manager |
| PRP | PeopleSoft Release Patchset | Maintenance artifact; not interchangeable with a VM image |
| FSS | OCI File Storage Service | Shared files; not a message broker or relational database |
| DB System | OCI database service resource | Different from an ordinary middle-tier compute VM |

Oracle defines topology nodes as VM abstractions with attributes such as OS, shape, disks, and installed components. Template and environment creation then select a topology and database source. [Topology overview](https://docs.oracle.com/en/applications/peoplesoft/cloud-manager/22/peoplesoft-cloud-manager-for-oracle-cloud-infrastructure/topology-overview.html), [environment creation](https://docs.oracle.com/en/applications/peoplesoft/cloud-manager/22/peoplesoft-cloud-manager-for-oracle-cloud-infrastructure/specifying-basic-environment-information.html)

## 12. Personal project narratives

For a confirmed release incident, see [Cloud Manager 16: OCI CLI dependency installation failure](Debugging_Stories.md#1-cloud-manager-16-oci-cli-dependency-installation-failure). The exact CLI version was pinned, but a newer related dependency release caused an installation issue. The remedy was prepackaging the CLI with its dependencies. Exact package names and versions remain unverified.

### Two-minute overview

“At Oracle, I worked on PeopleSoft Cloud Manager, which automates provisioning and lifecycle operations for PeopleSoft environments on OCI. The product serves 2,000+ customers, according to my project materials. My backend work used Python and Java alongside SQL, REST integrations, and infrastructure automation.

“The distributed aspect was coordination across OCI resources, VMs, database platforms, middleware, and search services. Those systems could complete or fail independently, so infrastructure creation alone was not enough to declare an environment ready.

“My contributions included clustered OpenSearch and reindexing, Exadata integration, a Vault-based credential framework, infrastructure automation, and CI/CD improvements. I would use one specific feature to explain the technical depth: its dependencies, communication path, failure handling, validation, and my individual ownership.”

Use this as an opening, then choose one contribution. Do not recite every technology without explaining a mechanism.

### OpenSearch deep dive

“I worked on the add-node functionality for OpenSearch integration in PeopleSoft Cloud Manager, enabling an additional node to be added to the search deployment. The feature sits across infrastructure provisioning, search-node configuration, and PeopleSoft integration. For an existing cluster, shard allocation and recovery are distinct from an application-data reindex. I recall an indexing step in our workflow; I would verify its implementation before naming the exact mechanism.”

Complete the story with your actual cluster roles, node count, DPK/release, node-join logic, failure handling, index-build method, and validation. An alias switch, custom change-data-capture pipeline, or zero-downtime migration is not established by your resume.

### Vault deep dive

“I designed a credential framework using OCI Vault to centralize secrets and automate rotation, recovery, and updates needed during scaling. The central challenge was keeping the authoritative credential and its distributed consumers consistent. I would explain the actual change order, validation, and recovery path, including how a new node obtained the current credential.”

Supply a real incident or edge case and the measurement behind the stated time savings.

### Exadata deep dive

“I helped deliver Exadata integration across releases. The important boundary was connecting PeopleSoft lifecycle management to a database platform with its own resources, credentials, and multi-node behavior. My role was [actual feature/module], and the key issue I solved was [actual failure or design constraint].”

Fill the brackets before practicing. Do not claim to have designed Oracle RAC, Exadata storage, or the entire database service when your contribution was integration.


## Study path

- [Architecture and data flow](02_Architecture_and_Data_Flow.md)
- [Engineering challenges](03_Engineering_Challenges.md)
- [Scaling and failure scenarios](04_Scaling_and_Failure_Scenarios.md)
- [Interview Q&A](05_Interview_QA.md)
- [Comprehensive technical reference](Cloud_Manager_Interview_Guide.md)
