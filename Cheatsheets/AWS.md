# AWS interview preparation

[Repository guide](../README.md) · [Networking fundamentals](../System_Design/Networking.md) · Related: [OCI vs. AWS](OCI_vs_AWS.md), [Terraform](Terraform.md), [Kubernetes](Kubernetes.md), [system design](../System_Design/README.md).

Focus first on EC2, S3, IAM, and the network/request path relevant to your experience. Other services below are interview knowledge and design alternatives, not claims that they were used in EventOps or Gordian. Service features, quotas, and availability vary; verify the deployed configuration rather than memorizing prices or defaults.

## Contents

- [AWS fundamentals](#aws-fundamentals)
- [Compute and scaling](#compute-and-scaling)
- [Storage and S3](#storage-and-s3)
- [Databases and caching](#databases-and-caching)
- [Identity and security](#identity-and-security)
- [Networking and security](#networking-and-security)
- [Messaging and background work](#messaging-and-background-work)
- [Operations, recovery, and cost](#operations-recovery-and-cost)
- [Practical interview scenarios](#practical-interview-scenarios)

## AWS fundamentals

### What are Regions, Availability Zones, and edge locations?

A Region is a geographic area containing Availability Zones. AZs provide separate infrastructure failure boundaries within a Region; design dependent tiers and capacity for the failure you intend to tolerate. Edge locations serve functions such as content delivery near users. Multi-AZ is not automatically multi-Region disaster recovery, and placing resources in two AZs is insufficient if shared dependencies still have a single point of failure.

### Shared responsibility: what do I operate?

AWS operates underlying cloud infrastructure; customers remain responsible for their data, identities, permissions, and configuration. With EC2, guest OS patching and application operations are customer concerns. Managed services shift some infrastructure work to AWS but do not remove application security, backup configuration, access control, or recovery validation. [AWS service overview](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html).

## Compute and scaling

### What are EC2, an AMI, and an instance type?

EC2 runs virtual servers. An AMI supplies an instance's launch image; an instance type determines resource characteristics such as CPU, memory, network, and storage capabilities. Keep images versioned, apply runtime configuration separately, and avoid embedding secrets. An image is not a complete recovery plan for changing application data. [EC2 concepts](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html).

### Load balancer vs. Auto Scaling Group?

A load balancer distributes traffic to eligible targets. An Auto Scaling Group manages a desired fleet and can replace unhealthy instances or adjust capacity under policy. Define health/readiness, startup time, draining, and downstream connection limits. Increasing app instances can saturate a shared database rather than improve throughput.

An ALB handles HTTP(S) application routing; an NLB handles transport-level workloads. Choose based on protocol, routing, connection, and operational requirements, not a claim that one is universally faster.

### EC2 vs. ECS/EKS vs. Lambda?

| Choice | Fits | Tradeoff |
|---|---|---|
| EC2 | VM control, existing services, long-running or specialized workloads | Own instance/software lifecycle and capacity |
| ECS / EKS | Managed container orchestration; EKS uses Kubernetes | Still own application configuration, resources, networking, and deployment behavior |
| Lambda | Event-driven functions within the selected execution model's constraints | Invocation/runtime/concurrency limits, cold-start and downstream capacity considerations |

A memory-heavy report is not automatically a good Lambda migration. Check measured memory, duration, data movement, retry behavior, and the specific execution model's limits. [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html). For Kubernetes mechanics use the [Kubernetes](Kubernetes.md).

## Storage and S3

### S3 vs. EBS vs. EFS?

| Service | Model / use | Boundary |
|---|---|---|
| S3 | Objects addressed by bucket/key; reports, uploads, artifacts | Not an ordinary shared POSIX filesystem |
| EBS | Block volumes for EC2 workloads | Attachment, AZ, persistence, and snapshot choices matter |
| EFS | Managed shared file storage | Access patterns, permissions, throughput, and network configuration matter |

EC2 instance-store data is ephemeral; use appropriate persistent storage for authoritative state. EBS deletion behavior depends on configuration, so “EC2 terminated” does not always mean “all storage deleted.”

### How do you store and deliver generated reports safely?

A worker renders to a temporary artifact, uploads to a stable job-scoped object key, confirms completion, and records readiness. A DB update and an S3 upload are not one transaction: use retry-safe identity and reconciliation for partial success.

For large reports, stream or multipart-upload instead of buffering the entire file. Define cleanup for abandoned multipart uploads and objects whose database/job update never completed.

Keep the bucket private. After checking user/object authorization, the backend can stream a report or issue a short-lived presigned URL. That URL is a bearer capability within its validity and permissions; do not log or expose it unnecessarily. Block Public Access and deliberate bucket policies help prevent unintended public access; encryption does not replace authorization. [Presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/ShareObjectPreSignedURL.html).

### Consistency, versioning, and lifecycle?

S3 provides strong read-after-write consistency for object writes/deletes and listing, but this does not make a multi-object or database-plus-object workflow atomic. Versioning can retain previous object versions; lifecycle policies can transition or expire eligible objects/versions. Define retention and restore expectations, including retrieval behavior of chosen archive classes. [S3 overview and consistency](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).

## Databases and caching

### RDS vs. a database on EC2 vs. DynamoDB?

RDS manages relational database infrastructure and selected maintenance capabilities; you still own schemas, queries, indexes, credentials, and application behavior. A database on EC2 gives more control and more operational responsibility. DynamoDB is a managed key-value/document service requiring deliberate key and access-pattern design; it is not a drop-in relational replacement.

### Multi-AZ vs. read replicas vs. backup?

Multi-AZ addresses availability/failover according to deployment type. A traditional RDS Multi-AZ DB instance has a standby that does not serve reads; RDS Multi-AZ DB clusters have readable standby instances. Read replicas can support read capacity with engine/configuration-specific lag and failover behavior. Backups restore a historical state; a replica can also replicate an unwanted change. [RDS deployment distinctions](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.html).

### Where does ElastiCache fit?

Managed cache infrastructure can reduce repeated reads or support shared short-lived state. Choose TTL, invalidation, availability, and memory policy deliberately. A cache is not automatically the source of truth or a replacement for database constraints. See [caching design](../System_Design/Caching_Performance.md).

## Identity and security

### IAM user, role, policy, and instance profile?

An IAM principal acts under permissions. A role supplies assumable identity and temporary credentials; policies describe allowed/denied actions under conditions. An instance profile associates a role with EC2. Prefer workload roles over baking long-lived access keys into images or code. The application's SDK must use the supported credential chain and refresh behavior. [EC2 role credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html).

### What do you check for AccessDenied?

Identify the actual caller, action, resource, and request context. Check applicable identity/resource policies, explicit denies, permission boundaries, organization policies, endpoint policies, and KMS permissions as relevant. An allowed network path does not grant API permission. Do not fix an unexplained denial with blanket administrator access.

### KMS vs. Secrets Manager vs. application authentication?

KMS manages cryptographic keys and operations. Secrets Manager stores/manages secrets and can participate in configured rotation workflows. IAM controls AWS access; the application's login and object authorization are separate. Rotation also requires updating the backing credential and its consumers; storing a new secret value alone is insufficient. See [credential rotation design](../System_Design/Cryptography_Passwords_Secrets.md#8-how-do-you-rotate-a-database-credential-without-downtime).

## Networking and security

The following examples retain AWS-specific configuration. Learn the provider-independent packet/request mechanisms in [Networking](../System_Design/Networking.md).

### 1. What are security rules inside an AWS network?

In an AWS VPC, **security groups** control traffic associated with resources such as EC2 network interfaces, and **network ACLs (NACLs)** filter traffic crossing subnet boundaries. Use these alongside routing, private subnets, and application authentication.

For IP/CIDR, ports, ingress/egress, routing, and transport fundamentals, see [Networking](../System_Design/Networking.md). Network reachability and application authorization are separate checks.

### 2. Security group vs. network ACL

| Property | Security group (SG) | Network ACL (NACL) |
|---|---|---|
| Boundary | Associated resource/network interface | Subnet boundary; does not filter traffic within the same subnet |
| Actions | Allow only; unmatched traffic is implicitly denied | Allow and deny |
| Connection tracking | Stateful: responses to allowed connections are automatically permitted | Stateless: return traffic requires explicit rules |
| Evaluation | All associated SG rules combine; there is no ordered deny rule | Lowest rule number first; first match wins; final `*` rule denies unmatched traffic |
| Rule peers | CIDRs, supported SG references, prefix lists | IP CIDRs; no SG references |
| Association | Multiple SGs can apply to a resource | One NACL per subnet; one NACL can serve multiple subnets |
| Main use | Fine-grained application-tier access | Additional subnet-level restrictions or explicit IP denies |

A newly created custom SG has no inbound rules and initially allows all outbound traffic. Remove the broad outbound rule if restricting egress. The VPC's **default SG** differs: it also permits inbound traffic from resources associated with that same SG. A default NACL initially permits traffic; a newly created custom NACL initially denies traffic until rules are added.

**Common trap:** a restrictive SG cannot cancel an allow in another attached SG. SG permissions are combined. A NACL deny can still block a connection that an SG allows. See [AWS SG rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html) and [AWS NACL behavior](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html).

### 3. Configure a three-tier application

```text
Internet client
    | HTTPS 443
    v
Public Application Load Balancer (alb-sg)
    | HTTP 8080 (example internal hop; use HTTPS where required)
    v
Private application servers (app-sg)
    | PostgreSQL 5432
    v
Private RDS database (db-sg)
```

Example SG rules, assuming these resources are in the same VPC:

| SG | Direction | Protocol / destination port | Source or destination | Reason |
|---|---|---|---|---|
| alb-sg | Ingress | TCP 443 | Source `0.0.0.0/0` | Public HTTPS; add `::/0` only if serving IPv6 |
| alb-sg | Egress | TCP 8080 | Destination `app-sg` | Forward requests and health checks on the example target port |
| app-sg | Ingress | TCP 8080 | Source `alb-sg` | Only the ALB reaches the app on this port |
| app-sg | Egress | TCP 5432 | Destination `db-sg` | App initiates database connections |
| db-sg | Ingress | TCP 5432 | Source `app-sg` | Database reachable only from app tier on this port |

These are the application data path rules, not a complete environment configuration. Add required outbound dependencies such as package repositories, external APIs, monitoring, or endpoints. Account for a separate health-check port if configured. Responses to allowed connections need no reverse SG rule; the database needs no outbound SG rule merely to reply to app queries.

An SG reference matches traffic associated with the referenced group's interfaces under AWS's supported reference behavior. It **does not copy the other group's rules**, create routes, or authorize database login. SGs do not provide TLS encryption.

**Console workflow:**

1. In VPC or EC2 → Security Groups, create `alb-sg`, `app-sg`, and `db-sg` in the intended VPC.
2. Edit inbound and outbound rules to implement the table; remove default allow-all egress when applying the restricted policy.
3. Associate each SG with the correct ALB, EC2 interfaces, or RDS database. Review every attached SG for broader permissions.
4. Confirm subnet routes, NACL associations, listeners, target ports, and application binding. Keep the database non-public.
5. Test both allowed paths and denied paths, then capture the configuration in Terraform/CloudFormation for repeatable review.

For admin access, use an approved private access path, such as a VPN or Systems Manager Session Manager. If SSH is required, restrict TCP 22 to the admin source rather than the internet. Session Manager requires IAM, an agent, and connectivity to its service endpoints.

### 4. Why do NACLs need ephemeral ports?

A client normally chooses a temporary **source port**, while the server listens on a well-known destination port:

```text
Request: client:55000 → server:443
Reply:   server:443   → client:55000
```

A server-subnet NACL needs ingress TCP 443 from the allowed client CIDR **and egress TCP to the client's ephemeral destination ports**. If the client is in another controlled subnet, that subnet needs matching outbound request and inbound response rules too.

Illustrative server-subnet NACL for HTTPS from one example client range:

| Direction | Rule number | Protocol / destination ports | Peer CIDR | Action |
|---|---|---|---|---|
| Inbound | 100 | TCP 443 | Source `203.0.113.0/24` | Allow |
| Outbound | 100 | TCP 1024–65535 | Destination `203.0.113.0/24` | Allow |
| Both | `*` | All remaining traffic | Any | Deny |

The broad ephemeral range is an example; choose the required range for the clients/services in the actual path. This table alone would block other dependencies. To deny a specific IP inside an allowed CIDR, place the deny at a lower number, such as 90. A deny at 200 is never reached for traffic already allowed at 100.

### 5. Routes, public/private subnets, and NAT

| Component | Responsibility |
|---|---|
| VPC | Logically isolated network with an IP address space |
| Subnet | Address range in one availability zone |
| Route table | Chooses the next hop for destination IP ranges |
| Internet gateway (IGW) | Enables internet connectivity for appropriately configured resources |
| Public subnet | Has a route to an IGW; direct internet IPv4 connectivity also requires appropriate public addressing and traffic rules |
| Private subnet | Has no direct route to an IGW |
| Public NAT gateway | Supports outbound IPv4 internet access from private resources through a public subnet/IGW, with replies; does not expose them to unsolicited inbound connections |
| VPC endpoint | Private access to supported services; endpoint type, routing, policies, and SG requirements vary |

Typical IPv4 setup: public subnet `0.0.0.0/0 → IGW`; private app subnet `0.0.0.0/0 → NAT gateway`. A database subnet can omit an internet default route. NAT is connectivity infrastructure, not a replacement for egress policy. Standard SG port/CIDR rules do not express arbitrary hostname allowlists.

**IAM vs. network access:** IAM controls who may invoke AWS APIs or change resources. SGs/NACLs control network traffic. Neither replaces application authentication or database permissions. AWS WAF filters supported HTTP(S) application traffic; it serves a different purpose from an SG port rule.

### 6. Debug “the port is open but it still times out”

1. Resolve DNS and confirm the destination IP and port.
2. Check routes and return routes, public addressing, IGW/NAT/endpoints as applicable.
3. Inspect SGs on both sides: sender egress and receiver ingress for the initiated connection.
4. Check NACLs at each crossed subnet boundary, including ephemeral return ports and rule order.
5. Check the OS firewall, listening socket, container mappings, ALB listener/target configuration, and health checks.
6. Use VPC Flow Logs to inspect accepted/rejected flows and Reachability Analyzer for supported configuration paths. An `ACCEPT` record does not prove application success; correlate with service logs and an actual connection test.

Example tests from an authorized source: `nc -vz <db-host> 5432` for TCP connectivity and `curl -v https://<app-host>` for HTTPS. Also test that an unrelated instance cannot access the database.

**Dig deeper:** SGs/NACLs cannot block DNS traffic to the Amazon-provided Route 53 Resolver; use Route 53 Resolver DNS Firewall for that filtering requirement. Removing an SG rule may not immediately terminate tracked connections; distinguish testing a new connection from an existing one.

### 7. Interview answer and follow-ups

> “In AWS, I use security groups for stateful resource-level traffic control and network ACLs for stateless subnet-level filtering. Ingress means incoming traffic and egress means outgoing traffic relative to the resource. I define the required paths first: HTTPS to the load balancer, the app port only from the load balancer's security group, and the database port only from the app's security group. I restrict new outbound connections to required dependencies. Security groups permit response traffic automatically; NACLs need explicit return-path rules, including ephemeral ports. I also verify routing, keep application and database tiers private, and validate with connection tests and VPC Flow Logs.”

| Interview follow-up | Key point |
|---|---|
| Can an SG explicitly deny an IP? | No. Use an appropriate NACL deny or other filtering control. |
| Do I need ingress ephemeral-port rules for replies to app-initiated HTTPS? | Not in its stateful SG; the relevant stateless NACLs need return-path rules. |
| Does allowing ingress 443 permit all outbound connections? | No. It permits replies to allowed inbound connections; new outbound connections need egress permission. |
| Why use SG references instead of instance IPs? | Express tier membership without tracking changing individual private IP addresses. |
| Is a private subnet enough to protect the DB? | No. Restrict SG access and use authentication, TLS, patching, and appropriate data permissions. |
| Does a public subnet make every instance public? | No. Routes, addressing, SGs/NACLs, and the listening service all matter. |
| Is Kubernetes Ingress the same concept? | No. Kubernetes Ingress is an HTTP(S) routing API implemented by a controller; inbound/ingress is a general traffic direction. |

## Messaging and background work

### SQS vs. SNS vs. EventBridge?

| Service | Role | Interview concern |
|---|---|---|
| SQS | Queue work for consumers | Visibility, redelivery, idempotency, backlog, poison messages |
| SNS | Publish notifications to subscribed destinations | Delivery behavior varies by protocol/subscription |
| EventBridge | Route events under rules/integration contracts | Schema, retry, ordering, target behavior, and replay configuration |

Standard SQS delivery can repeat a message; consumers must tolerate duplicates. Visibility timeout temporarily hides a received message; it does not prove completion. Delete after the required work succeeds, and handle long tasks, retries, and DLQ redrive deliberately. FIFO features do not make arbitrary database writes or external side effects exactly-once. [SQS delivery](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html).

### How would you scale report workers?

Queue small job/input references, not whole datasets. Scale against backlog age, arrival rate, processing time, memory, and downstream capacity. Use stable job IDs and retry-safe artifact publication. Keep worker scaling separate from interactive API scaling. See [large-data processing](../System_Design/Large_Data_Background_Processing.md).

## Operations, recovery, and cost

### CloudWatch vs. CloudTrail?

CloudWatch collects operational telemetry such as metrics/logs and supports alarms. CloudTrail records AWS account activity, including management and configured data events; event coverage/configuration matters. Use operational signals to diagnose latency/failures and audit events to investigate resource/API actions. Neither replaces application-level authorization or a complete business audit trail. [CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html), [CloudTrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html).

### How do you deploy and recover?

Use versioned artifacts/configuration, staged rollout, health checks, compatible database migrations, and a defined rollback/forward-repair path. Set recovery time and recovery point objectives, then test restores and dependency recovery. Multi-AZ deployment, replication, backups, and multi-Region recovery address different failures.

### How do you reduce cost without harming reliability?

Measure spend by owner/workload and resource category. Consider right-sizing, idle-resource cleanup, storage lifecycle, data transfer/NAT costs, unnecessary repeated work, and suitable purchasing commitments. Keep headroom and retention/recovery requirements. The 25% cost reduction in the PeopleSoft materials was an OCI result; do not relabel it as an AWS saving. [Infrastructure and cost tradeoffs](../System_Design/Infrastructure_Automation.md#images-patching-cleanup-and-cost).

## Practical interview scenarios

| Question | Answer direction |
|---|---|
| EC2 application cannot upload a report to S3 | Separate DNS/routes/endpoints from actual IAM principal, bucket/endpoint policy, and encryption-key permissions |
| ALB returns 502 or 504 | Inspect target health, listener/target protocol, upstream binding, timeout budgets, and application logs |
| S3 object exists but a user receives AccessDenied | Check intended delivery method, signer/caller permissions, expiry, policies, and applicable KMS access |
| App scales out but latency worsens | Investigate DB pools/locks, shared dependencies, cache misses, and worker contention |
| Worker completes but receives the same message again | Idempotent job identity, completion record, artifact checks, acknowledgement/delete boundary |
| An AZ fails | Explain surviving capacity, load-balancer targets, DB failover, and external dependencies |
| Restore succeeds but application fails | Check credentials, endpoints, configuration, schema compatibility, and representative business operations |

**Experience connection:** EventOps documents EC2 hosting and S3 report uploads; Gordian documents EC2 hosting. Describe the exact services you used separately from these proposed architectures. Missing historical configuration belongs in the [project recall checklist](../Projects/README.md#details-to-recall).

## AWS networking references

- [AWS security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)
- [Security group rules and references](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
- [Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)
- [Compare SGs and NACLs](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html)
- [NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)
- [Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html)
