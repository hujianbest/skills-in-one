# NFR Quality Attribute Scenario Review Excerpt

Spec review checks that embedded NFRs are written as quality attribute scenarios with stimulus source, stimulus, environment, response, and response measure.

- Response Measure needs a threshold or observable pass/fail criterion.
- Acceptance criteria must match the QAS and not introduce a different metric.
- Split NFRs that mix latency, memory, concurrency, availability, safety, or security into one row.
- Missing thresholds or operating conditions are USER-INPUT / TEAM-EXPERT, not reviewer guesses.
