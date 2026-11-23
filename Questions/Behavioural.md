# Behavioural Interview Questions

Use the STAR structure (Situation, Task, Action, Result). Keep the setup brief, spend most of the answer on your decisions and actions, and close with an outcome you can support. The sample answers below are hypothetical. Replace the details with your own experience and use metrics only when you can explain how they were measured.

## Ownership and judgement

### 1. Tell me about a production incident you owned.

**Sample answer.** “A batch job failed after a release and delayed a report used by operations. I took ownership of recovery, paused retries while we checked for partial writes, and asked a teammate to trace the failing input while I verified the last successful checkpoint. I gave operations a recovery update and replayed only the affected batch once we confirmed it was safe. We reconciled the report totals before handing it back. I then added a preflight validation check for the failure we’d missed.”

### 2. Tell me about a mistake you made and what you learned.

**Sample answer.** “I underestimated how long a data migration would hold locks because I tested it on a small dataset. When I saw write latency rise, I paused the rollout and explained the impact to the team. I rehearsed a batched backfill on representative data and set a threshold that would pause it if latency rose again. The migration completed within that limit, and we added a data-volume check to our release process.”

### 3. Describe a time you made a difficult tradeoff under a deadline.

**Sample answer.** “We had to meet a launch date, but the planned reporting feature required a schema change we hadn’t tested at production volume. I proposed shipping the core workflow and using an existing export for the first reporting cycle. I agreed on the temporary process with operations and documented when we’d retire it. We met the launch date and rolled out the reporting change after verifying it on representative data.”

## Collaboration and leadership

### 4. Tell me about a technical disagreement with a teammate.

**Sample answer.** “A teammate proposed a new service to isolate report generation. I was concerned about the deployment and on-call overhead. We agreed on what mattered most: queue isolation, ownership, and recovery after a worker failure. I prototyped dedicated workers in the existing application while my teammate mapped the service boundaries. We chose the worker approach for the release and agreed on when we’d revisit the decision.”

### 5. Tell me about a time you influenced a decision without authority.

**Sample answer.** “Several teams were shipping API changes independently, and consumers were finding compatibility issues after deployment. I used one incident to show where a contract test would have caught the break, then added an example to our CI pipeline. I asked a consuming team to help choose the first contract to test. Once the check was easy to adopt, other teams copied it for their endpoints.”

### 6. Describe a time you helped a teammate develop a skill.

**Sample answer.** “A teammate wanted to get better at diagnosing slow queries. I paired with them on a real report and asked them to predict which part of the plan was expensive before we checked the row counts. They proposed an index and measured the before-and-after performance. On the next report, they led the investigation and walked the team through the tradeoffs.”

## Communication and ambiguity

### 7. Tell me about a time you handled unclear requirements.

**Sample answer.** “A stakeholder asked for faster reports, but the request didn’t specify which report mattered or how fresh the data had to be. I watched the operations team run their morning workflow and learned that one summary was blocking the rest of their work. We agreed on a latency and freshness target for that report. I tested a precomputed summary and demonstrated both the faster load time and when the data refreshed.”

### 8. Tell me about difficult feedback you received and acted on.

**Sample answer.** “My manager told me that my incident updates were technically accurate but hard for support to act on. I asked support what they needed and changed my updates to lead with customer impact, the current workaround, and when to expect another update. I kept detailed diagnosis in the incident channel. In the next incident, support could brief customers without waiting for a separate explanation.”

Use the [project interview guides](../Projects/README.md) to find real examples you can adapt. For each story, prepare a follow-up on what you personally did, why you chose that approach, and what you’d change next time.
