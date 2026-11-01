# Networking: fundamentals and system-design interviews

[Study index](README.md) · Related: [AWS](../Cheatsheets/AWS.md), [REST APIs](REST_API_Design.md), [distributed systems](Distributed_Systems.md), [observability](Observability.md).

Use this guide for provider-independent mechanisms and diagnosis. AWS resource configuration belongs in the AWS guide; HTTP endpoint design and authentication have their own linked guides.

## Contents

- [Request journey](#what-happens-when-you-enter-an-https-url)
- [Layers and protocols](#which-network-layers-matter-in-an-interview)
- [TCP, UDP, and QUIC](#tcp-vs-udp-and-where-does-quic-fit)
- [IP, subnets, CIDR, and ports](#ip-subnets-cidr-and-ports)
- [DNS](#how-does-dns-resolution-work)
- [TLS](#what-does-tls-protect)
- [HTTP connections](#http-versions-and-connection-reuse)
- [Proxies, load balancers, and discovery](#reverse-proxy-load-balancer-cdn-and-service-discovery)
- [Routing, NAT, and firewalls](#routes-nat-firewalls-and-private-networks)
- [Latency and retries](#latency-throughput-timeouts-and-retries)
- [Troubleshooting](#how-do-you-debug-a-failed-or-slow-request)
- [Interview drills](#interview-drills)

## What happens when you enter an HTTPS URL?

**Interview answer:** The browser checks applicable caches and resolves the hostname when necessary. It establishes or reuses a suitable connection, negotiates transport security, sends an HTTP request, and receives a response. A CDN/proxy/load balancer may forward the request to an application that calls other services or a database. The browser then processes the response and may fetch more resources.

```text
Browser → DNS resolution → connection + TLS → CDN / reverse proxy / load balancer
        → application → database / dependencies
        ← HTTP status, headers, body ← response path
```

This is a logical sequence: caches, connection reuse, proxies, redirects, and HTTP/3 change the actual steps. DNS need not run for every request, and TCP is not required for HTTP/3. Backend processing time is only one part of user-visible latency. [Browser request and rendering overview](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work).

## Which network layers matter in an interview?

| Layer / responsibility | Examples | Typical failure |
|---|---|---|
| Local link | Ethernet, Wi-Fi, local neighbor delivery | Local connectivity or interface problem |
| Network addressing/routing | IPv4/IPv6, IP routes | No route, unreachable destination, wrong address |
| Transport | TCP, UDP | Connection refused, packet loss, exhausted sockets |
| Transport security | TLS over a suitable transport; integrated with QUIC | Certificate, hostname, trust, or protocol failure |
| Application | HTTP, DNS protocols, database protocols | HTTP error, invalid request, database authentication failure |

The OSI model is a vocabulary for responsibilities, not a requirement that every real protocol fits one box perfectly. “Layer 4 load balancing” generally means transport-level handling; “Layer 7” understands application requests such as HTTP paths and headers.

## TCP vs. UDP, and where does QUIC fit?

| Mechanism | Provides | Important limitation / use |
|---|---|---|
| TCP | Connection-oriented, reliable ordered byte stream with flow/congestion control | Does not preserve application message boundaries or prove business success |
| UDP | Datagram transport preserving datagram boundaries | Delivery/order/deduplication are not guaranteed by UDP itself |
| QUIC | Secure transport over UDP with reliable streams and connection migration | Higher-level guarantees come from QUIC, not bare UDP; network support still matters |

**TCP setup:** a typical handshake is SYN → SYN-ACK → ACK. Connection setup, TLS negotiation, and application authentication are separate milestones. One socket `send` need not correspond to one peer `read`; applications need framing.

**Reliability trap:** a connection reset or timeout can happen after the server commits a write. TCP reliability does not provide exactly-once business operations. See [TCP specification](https://www.rfc-editor.org/rfc/rfc9293.html) and [QUIC specification](https://www.rfc-editor.org/rfc/rfc9000.html).

## IP, subnets, CIDR, and ports

An IP address identifies a network interface/addressable endpoint in a network context. A subnet groups addresses under a prefix; routers choose next hops based on destination prefixes. IPv4 NAT can translate internal addresses/ports at a boundary.

| Term | Example / answer |
|---|---|
| CIDR | `10.0.1.0/24` fixes 24 of 32 IPv4 bits, covering 256 addresses; usable-host rules depend on the network/provider |
| Single IPv4 address | `/32`; `203.0.113.10/32` is a documentation example |
| Default destination | `0.0.0.0/0` for IPv4, `::/0` for IPv6 |
| Listening port | Server application bound to TCP 443, for example |
| Ephemeral port | Client-selected temporary source port, such as 55000 |
| Loopback binding | Listening on `127.0.0.1` normally does not expose the service on an external interface |
| Ingress / egress | Incoming / outgoing traffic relative to the specific boundary |

```text
Request: client:55000 → server:443
Reply:   server:443   → client:55000
```

A socket connection is distinguished by protocol and endpoint address/port pairs. Hundreds of clients can connect to the same server port. A firewall allow rule does not start a listener, publish a container port, or establish a route.

## How does DNS resolution work?

**Interview answer:** DNS maps names to records. A client typically asks a recursive resolver, which uses cached answers or follows the DNS delegation hierarchy to authoritative servers. Caches retain records according to TTL and policy; changing authoritative data does not immediately replace every cached answer.

| Record | Purpose |
|---|---|
| A / AAAA | IPv4 / IPv6 address |
| CNAME | Alias to another DNS name |
| MX | Mail exchange |
| TXT | Text records used by various verification/policy schemes |
| NS | Authoritative nameserver delegation |

**Traps:** DNS success does not establish TCP connectivity or application health. DNS-based failover is affected by caching and existing connections. Split-horizon/private DNS can give different answers inside and outside a network. DNS uses more than UDP alone: TCP and encrypted transports are also relevant. [DNS concepts](https://www.rfc-editor.org/rfc/rfc1034.html).

## What does TLS protect?

TLS provides transport confidentiality and integrity and commonly authenticates the server using a certificate validated against a trusted chain and hostname. Mutual TLS additionally authenticates clients through certificates. The HTTP request's authorization remains a separate application decision.

**Termination:** if TLS ends at a load balancer, its connection to the backend is a separate hop with its own encryption/authentication configuration. An external HTTPS URL does not prove that every internal hop is encrypted.

**Failure checks:** hostname mismatch, expired certificate, incomplete/untrusted chain, clock error, unsupported protocol, and incorrect SNI/certificate selection. Disabling verification hides the problem rather than establishing a trustworthy connection. [TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html).

## HTTP versions and connection reuse

| Version | Interview distinction |
|---|---|
| HTTP/1.1 | Persistent connections; concurrency often uses several connections |
| HTTP/2 | Multiplexes streams over a TCP connection; transport packet loss can delay all its streams |
| HTTP/3 | Uses QUIC; loss on one stream does not create TCP's cross-stream ordered-delivery blocking, although congestion and shared resources still affect performance |

Connection pools reuse expensive connections. Oversized pools can overload a database; undersized pools can queue requests. Keep-alive idle lifetimes should align across clients, proxies, and servers to avoid stale-connection surprises. HTTP statelessness does not mean no connections or no application session state. See [HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview).

## Reverse proxy, load balancer, CDN, and service discovery

For configuration and Nginx-specific diagnosis, use [Nginx](../Cheatsheets/Nginx.md).

| Component | Responsibility | Trap |
|---|---|---|
| Reverse proxy | Accept client traffic on behalf of upstream applications | Proxy success does not prove downstream business success |
| Load balancer | Distribute eligible requests/connections across targets | Health checks and draining need deliberate configuration |
| Forward proxy | Act on behalf of clients making outbound requests | Its DNS, trust, and network path can differ from the client's |
| CDN | Cache/distribute eligible content near users | Private content, cache keys, TTL, and invalidation need care |
| Service discovery | Resolve logical service identities to endpoints | Endpoint caches and membership changes can become stale |

A product may combine several roles. L7 routing can select services by path; L4 routing works at the transport level. Sticky sessions can help a legacy design but introduce balancing/failover constraints. Prefer explicitly shared session state or suitable stateless handling when possible. Trust forwarded client headers only from controlled proxies; arbitrary client headers must not define identity or authorization.

## Routes, NAT, firewalls, and private networks

**Route:** selects a destination's next hop. **Firewall:** permits/denies traffic under its rules. **NAT:** translates addresses/ports. **Authentication:** establishes identity. These solve separate requirements.

Stateful filters track allowed connections and normally permit their replies; stateless filters need explicit return-path rules. Verify each product's connection-tracking behavior. A private address alone does not prevent access from connected or compromised systems; segmentation, identity, TLS, and least privilege remain necessary.

For a three-tier design, document client → entry point, entry point → app, and app → database paths. For each path specify source, destination, transport, destination port, return path, DNS, and application permissions. AWS-specific SG/NACL tables belong in [AWS networking and security](../Cheatsheets/AWS.md#networking-and-security).

## Latency, throughput, timeouts, and retries

Latency measures time per operation; throughput measures completed work per unit time. More bandwidth does not remove propagation delays, round trips, or slow dependencies. Tail latency matters when a request fans out to several services.

```text
Request budget ≈ DNS + connection/TLS + queueing + application/dependencies + transfer
```

The sum is a reasoning aid; reuse, parallel work, and overlap alter the actual path. Measure stages instead of assuming all delay is the network.

Use separate connection/read/overall budgets where the client supports them. Bound retries with backoff and jitter, respect the total deadline, and retry side effects only with appropriate idempotency/reconciliation. A read timeout can follow a committed write. A retry storm can amplify an outage. See [distributed failure handling](Distributed_Systems.md).

## How do you debug a failed or slow request?

| Symptom | Start checking |
|---|---|
| Name resolution error | Hostname, resolver, private/public context, cache/TTL |
| Connection refused | Correct address/port, listening process, binding, active rejection |
| Connection timeout | Route/return route, filtering, target health, packet loss; timeout alone does not identify the cause |
| TLS handshake error | Hostname/certificate chain/expiry, SNI, client trust and versions |
| HTTP 401 / 403 | Authentication/authorization and applicable proxy policies; transport reached an HTTP responder |
| HTTP 502 / 504 | Gateway's upstream connection/protocol/response or timeout; correlate backend logs |
| Slow only under concurrency | Pool waits, socket limits, queueing, CPU, downstream limits, retransmissions |

From an authorized diagnostic environment, illustrative read-only checks include:

```sh
nslookup example.com
curl -v --connect-timeout 3 --max-time 10 https://example.com/
openssl s_client -connect example.com:443 -servername example.com
```

Use platform-appropriate listener/route tools as well. Verbose headers/certificates or packet captures can contain sensitive data; collect only what the investigation needs. Ping success does not prove an application port works, and ping failure does not prove the host is down. Browser CORS errors are a separate response-access policy, not a general network firewall.

## Interview drills

1. Draw an HTTPS request through DNS, TLS, a load balancer, app, and database; mark each latency/failure boundary.
2. Explain why a public endpoint works from your laptop but fails from a private worker.
3. Diagnose a working TCP connection followed by a TLS failure, then a successful TLS connection followed by HTTP 403.
4. Explain ephemeral return ports to someone configuring a stateless firewall.
5. Handle a payment request whose response is lost after the server commits.
6. Trace an application slowdown caused by connection-pool waits rather than network bandwidth.

Use the [AWS guide](../Cheatsheets/AWS.md) to translate these mechanisms into cloud resources, then connect them to an actual project request path.
