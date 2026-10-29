# AWS Networking and Security Interview Cheat Sheet

[Study index](README.md) · Related: [cloud and Kubernetes](Cloud_Kubernetes_CheatSheet.md), [infrastructure automation](Infrastructure_Automation_CheatSheet.md), [OCI vs. AWS](OCI_vs_AWS_Interview_Guide.md).

## 1. What are security rules inside an AWS network?

In an AWS VPC, **security groups** control traffic associated with resources such as EC2 network interfaces, and **network ACLs (NACLs)** filter traffic crossing subnet boundaries. Use these alongside routing, private subnets, and application authentication.

- **Ingress / inbound:** traffic entering the resource or subnet being discussed.
- **Egress / outbound:** traffic leaving that resource or subnet.
- **Protocol:** TCP, UDP, or ICMP. TCP/UDP rules specify destination ports; ICMP uses types/codes.
- **Source:** where incoming traffic originates. **Destination:** where outgoing traffic goes.
- **CIDR:** an IP range. `10.0.1.0/24` spans 256 IPv4 addresses; `203.0.113.10/32` is one example address. `0.0.0.0/0` means any IPv4 address; `::/0` means any IPv6 address.

Direction is relative: app → database is **egress at the app** and **ingress at the database**. A port rule does not start a service or establish a network route.

## 2. Security group vs. network ACL

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

## 3. Configure a three-tier application

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

## 4. Why do NACLs need ephemeral ports?

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

## 5. Routes, public/private subnets, and NAT

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

## 6. Debug “the port is open but it still times out”

1. Resolve DNS and confirm the destination IP and port.
2. Check routes and return routes, public addressing, IGW/NAT/endpoints as applicable.
3. Inspect SGs on both sides: sender egress and receiver ingress for the initiated connection.
4. Check NACLs at each crossed subnet boundary, including ephemeral return ports and rule order.
5. Check the OS firewall, listening socket, container mappings, ALB listener/target configuration, and health checks.
6. Use VPC Flow Logs to inspect accepted/rejected flows and Reachability Analyzer for supported configuration paths. An `ACCEPT` record does not prove application success; correlate with service logs and an actual connection test.

Example tests from an authorized source: `nc -vz <db-host> 5432` for TCP connectivity and `curl -v https://<app-host>` for HTTPS. Also test that an unrelated instance cannot access the database.

**Dig deeper:** SGs/NACLs cannot block DNS traffic to the Amazon-provided Route 53 Resolver; use Route 53 Resolver DNS Firewall for that filtering requirement. Removing an SG rule may not immediately terminate tracked connections; distinguish testing a new connection from an existing one.

## 7. Interview answer and follow-ups

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

## References

- [AWS security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)
- [Security group rules and references](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html)
- [Network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html)
- [Compare SGs and NACLs](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html)
- [NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html)
- [Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html)
