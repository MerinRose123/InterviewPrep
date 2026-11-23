# Behavioural Interview Questions

## 1. Tell me about a feature or project you built from scratch. How did you design the architecture, what tradeoffs did you make, and how did you handle edge cases?

**Starting point.** “On EventOps, I worked on scheduling that took participant availability into account. The feature needed to account for availability when users scheduled an event.”

Build out the answer with the part you owned, the data and request flow, where the availability check ran, and what happened when a booking was saved. Explain one design decision you actually made and the alternative you considered. For example, checking availability at submission improves freshness but adds work to the request. If requests can overlap, explain how you handled a slot becoming unavailable between the check and the save. Prepare to discuss missing availability and time-zone boundaries if they applied. Close with how you tested the behaviour and what you observed after rollout.

[EventOps contributions](../Projects/EventOps/01_Project_Overview.md#my-contributions) · [EventOps engineering challenges](../Projects/EventOps/03_Engineering_Challenges.md)

## 2. Tell me about a disagreement you had with a manager or teammate. How did you handle it, and what was the outcome?

**Answer structure.** “We disagreed about [specific decision]. I favoured [your approach] because [reason], while my manager or teammate was concerned about [their reason]. I asked what constraint mattered most, and we compared the options against [shared goal or evidence]. We decided to [decision]. I supported the decision by [your action], and the result was [observed outcome].”

Choose a real disagreement, even if the team ultimately chose the other approach. Explain what you did to move the decision forward and how you worked with the person afterwards.

## 3. Tell me about a production issue you encountered. How did you handle it?

**Answer structure.** Start with the production symptom and who was affected. Explain what you did first to contain the impact, how you communicated progress, and which evidence identified the cause. Describe your role in the fix, how you verified recovery, and what you changed to prevent recurrence.

**Related release example.** “During the Cloud Manager 16 release, installation failed even though the OCI CLI version was pinned. A newer release of a related dependency caused the failure. We resolved it by prepackaging the CLI with its dependencies so deployment used a controlled dependency set.” This is a documented release failure. If the interviewer asks specifically for a live production incident, prepare an example with confirmed production impact.

[Cloud Manager debugging stories](../Projects/PeopleSoft/Debugging_Stories.md)

## 4. When you encounter a bug, how do you troubleshoot it?

**Sample answer.** “I first clarify the expected behaviour and establish the scope. I capture a failing input, the environment, and a request or job ID, then compare a failing case with a successful one. I follow the request through logs, traces, and relevant data, and check recent code, configuration, and data changes. I test one hypothesis at a time. If I can’t reproduce it locally, I look for a difference in the data, environment, or timing and add targeted instrumentation if needed.

“For a live issue, I contain the impact while investigating. Once I isolate the cause, I reproduce it in a regression test where feasible, make the smallest fix that addresses it, and verify the original failure and nearby edge cases. After deployment, I check that errors stay down and the affected workflow behaves correctly.”

## 5. Tell me about a time you mentored a teammate or led a feature. How did you help others succeed, and what was the outcome?

**Feature leadership starting point.** “On EventOps, I improved the pytest setup and expanded coverage in important areas from about 40% to 70%. I used mocking to test behaviour that depended on external collaborators.” If you led this work, explain how you chose the first areas to cover, coordinated contributions, and helped teammates use the setup. Close with the coverage gain and any team outcome you can verify.

**Mentoring answer structure.** Describe what your teammate wanted to learn, how you adapted your support, and when you handed the work back. Close with something they could do independently afterwards.

[EventOps contributions](../Projects/EventOps/01_Project_Overview.md#my-contributions)
