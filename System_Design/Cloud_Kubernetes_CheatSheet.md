# Cloud and Kubernetes Interview Cheat Sheet

[Study index](README.md) · Related: [infrastructure automation](Infrastructure_Automation_CheatSheet.md), [observability](Observability_CheatSheet.md), [security](Multi_Tenancy_Security_CheatSheet.md), [AWS networking and security](AWS_Networking_Security_CheatSheet.md).

YAML and commands are illustrative; do not apply them to a cluster without adapting images, resources, networking, permissions, and version support.

## Contents

- [1. Object vs. block vs. file storage?](#1-object-vs-block-vs-file-storage)
- [2. Container vs. VM? What persists when a container restarts?](#2-container-vs-vm-what-persists-when-a-container-restarts)
- [3. Explain Kubernetes architecture](#3-explain-kubernetes-architecture)
- [4. Pod vs. Deployment vs. StatefulSet vs. Job?](#4-pod-vs-deployment-vs-statefulset-vs-job)
- [5. Requests, limits, probes, and shutdown?](#5-requests-limits-probes-and-shutdown)
- [6. How do HPA and node autoscaling differ?](#6-how-do-hpa-and-node-autoscaling-differ)
- [7. DNS, service discovery, load balancing, and TLS?](#7-dns-service-discovery-load-balancing-and-tls)
- [8. Availability zones, regions, deployments, and disaster recovery?](#8-availability-zones-regions-deployments-and-disaster-recovery)
- [References](#references)

## 1. Object vs. block vs. file storage?

| Storage | Access model / fit | Tradeoff |
|---|---|---|
| Object | Key + bytes + metadata; exports, backups, static assets | Not a general POSIX filesystem; request/egress and multipart costs |
| Block | Volumes to format/mount; databases | Attachment, capacity, durability, and zone constraints |
| File | Shared directory/filesystem semantics | Metadata scaling, locking, and network dependency |

For a large export, put bytes in object storage and persist ownership/status/object key in the DB. Stream/multipart-upload rather than buffering the entire file. Authorize before issuing a short-lived signed URL; a signed URL is a bearer capability until its validity ends under provider rules.

**Dig deeper:** object consistency is provider/operation specific; do not repeat “all object storage is eventually consistent.” S3 provides strong consistency for specified object operations, but that does not create a transaction across SQL and object storage. How do you clean up abandoned multipart uploads and orphaned objects? [S3 overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).

## 2. Container vs. VM? What persists when a container restarts?

Containers share the host kernel with process/resource isolation; VMs run guest kernels over virtualized hardware. An image is a packaged filesystem/configuration, not a running VM. Writable container layers are not a durable application data strategy; use appropriate volumes/external storage.

| Choice | Benefit | Risk / cost |
|---|---|---|
| Container | Fast deployment, consistent packaging | Kernel/runtime security and resource limits |
| VM | Stronger separate OS boundary and flexible guest OS | More OS management/startup/resource overhead |
| Managed service | Less operational responsibility | Service constraints, cost, provider dependency |

**Dig deeper:** build reproducibly, scan dependencies, pin images by digest for releases, run with minimal privileges, and separate secrets from images. How do native-library leaks affect container RSS even if the application heap looks stable?

## 3. Explain Kubernetes architecture

```text
User/CI -> API server -> admission/authz -> persisted desired state in etcd
                         ^                   |
                         | controllers reconcile desired vs observed state
Scheduler -> assigns unscheduled Pods to nodes
Node: kubelet -> container runtime (CRI) -> containers in Pods
Networking: CNI implementation; Service routing via kube-proxy or replacement
```

| Component | Responsibility |
|---|---|
| API server | Cluster API and control-plane access |
| etcd | Durable cluster state store; protect backups and access |
| Scheduler | Placement using resource/constraint information |
| Controller manager | Reconciliation loops such as replica management |
| kubelet | Node agent ensuring assigned Pod containers run |
| Container runtime | Pull/run containers through supported runtime integration |
| Cluster DNS / Service dataplane | Name resolution and stable service access |

The control plane is not on every application packet's critical path. Existing workloads may continue during a control-plane outage, while scheduling/reconciliation changes can stop. [Kubernetes components](https://kubernetes.io/docs/concepts/overview/components/).

**Dig deeper:** what happens if a node dies? Which controller replaces Pods? What if etcd loses quorum? Why are an etcd snapshot and a database-volume backup different recovery artifacts?

## 4. Pod vs. Deployment vs. StatefulSet vs. Job?

| Object | Use | Limitation |
|---|---|---|
| Pod | Co-scheduled containers sharing network/volumes | Ephemeral instance, not a rollout strategy |
| Deployment | Replicated replaceable application Pods | Does not supply application-level data consistency |
| StatefulSet | Stable identities and associated storage patterns | Does not automatically make a database correctly replicated |
| Job / CronJob | Finite / scheduled work | Duplicates/overlap/failure require idempotent job design |
| DaemonSet | Node-local agents | Node footprint and privileges |

**Dig deeper:** multiple containers in one Pod share an IP; a sidecar has coupled lifecycle/resource effects. Why shouldn't a long-lived user export depend on one specific Pod surviving?

## 5. Requests, limits, probes, and shutdown?

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
spec:
  replicas: 3
  selector:
    matchLabels: {app: orders}
  template:
    metadata:
      labels: {app: orders}
    spec:
      terminationGracePeriodSeconds: 40
      containers:
        - name: api
          image: example.invalid/orders:reviewed-version
          ports:
            - containerPort: 8080
          resources:
            requests: {cpu: "250m", memory: "256Mi"}
            limits: {cpu: "1", memory: "512Mi"}
          readinessProbe:
            httpGet: {path: /ready, port: 8080}
          livenessProbe:
            httpGet: {path: /live, port: 8080}
          startupProbe:
            httpGet: {path: /live, port: 8080}
            failureThreshold: 30
            periodSeconds: 5
```

Requests inform scheduling; limits constrain consumption with resource-specific behavior. CPU limits can throttle; memory exhaustion can cause OOM termination. Readiness affects traffic eligibility, liveness restarts unhealthy containers, startup probes protect slow startup from early liveness checks.

**Dig deeper:** shared DB failure should not normally make all instances fail liveness and restart together. During termination, stop accepting new work, drain in-flight requests/tasks, and finish or relinquish jobs within the grace period. A PodDisruptionBudget addresses eligible voluntary disruptions, not all failures.

## 6. How do HPA and node autoscaling differ?

HPA adjusts workload replica counts using configured metrics; node autoscaling adjusts infrastructure capacity. HPA does not guarantee new Pods can schedule or that the DB can absorb more clients. CPU utilization targets depend on the relevant resource requests.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orders
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: orders}
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: {type: Utilization, averageUtilization: 65}
```

For workers, backlog age/work per second may be more meaningful than CPU. Account for startup time, stabilization, scale-down drain, metric outages, and provider quotas. [HPA behavior](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/).

**Dig deeper:** ten Pods × twenty DB connections = up to 200 connections, before other services. How do you cap concurrency at the downstream capacity?

## 7. DNS, service discovery, load balancing, and TLS?

| Layer | Responsibility | Failure to investigate |
|---|---|---|
| DNS | Name to address/service lookup | Stale/negative caching, resolver latency |
| L4 load balancer | Connection-level routing | Long connections can skew load |
| L7 proxy/gateway | HTTP routing, termination, policy | Header handling, body size, timeout mismatch |
| Kubernetes Service | Stable virtual access to selected endpoints | Label/endpoint/readiness mismatch |
| Ingress / Gateway implementation | External application routing | Controller/provider must implement configuration |

Trace browser → DNS → TCP/TLS → load balancer → proxy → Service/Pod → DB. Know TLS termination points and whether internal hops are encrypted/authenticated. Connection pooling amortizes setup but needs limits and timeouts.

**Dig deeper:** DNS round-robin is not a complete health-aware routing system. Why do idle timeouts break WebSockets? Why can Nginx return 502 vs. 504? Investigate upstream connectivity vs. timeout rather than guessing.

## 8. Availability zones, regions, deployments, and disaster recovery?

| Strategy | Strength | Cost / risk |
|---|---|---|
| Rolling rollout | Gradual replacement | Requires old/new API and schema compatibility |
| Blue/green | Fast traffic switch | Duplicate capacity; DB changes still need compatibility |
| Canary | Limit exposure and compare signals | Traffic routing and evaluation complexity |
| Multi-zone | Survive selected zone failures | Cross-zone latency/cost; quorum placement |
| Multi-region DR | Recover larger failures | Replication lag, routing, data ownership, and testing |

Define RPO (acceptable data loss) and RTO (recovery time). Rehearse restore with infrastructure, DB, object data, keys, DNS, and application versions. A backup is not a recovery plan until restoration is verified. Multi-region active-active is a major consistency and conflict-resolution commitment.

**Resume drill:** explain actual OCI/AWS components, failure domains, traffic path, rollout ownership, and cost constraints. Do not claim Kubernetes production ownership merely because you understand its architecture.

## References

- [Kubernetes components](https://kubernetes.io/docs/concepts/overview/components/)
- [Kubernetes architecture](https://kubernetes.io/docs/concepts/architecture/)
- [Resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
- [Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
- [HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)
- [S3 overview and consistency](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
