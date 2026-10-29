# peoplesoft — scaling and failure scenarios

The [engineering challenge guide](03_Engineering_Challenges.md) contains detailed failure and recovery discussions. Use the [architecture diagrams](02_Architecture_and_Data_Flow.md) to walk through component boundaries, retries, consistency, and capacity.

## Whiteboard checklist

1. Identify source of truth and state ownership.
2. Mark synchronous calls and asynchronous work.
3. Explain behavior on timeout, duplicate request, crash, and partial success.
4. Discuss scaling bottlenecks and backpressure.
5. Specify health, latency, throughput, memory, and error metrics.
