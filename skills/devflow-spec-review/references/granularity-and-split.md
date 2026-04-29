# Granularity And Split Review Excerpt

Spec review checks that requirement rows and SR AR candidates are small enough to design, review, implement, and verify independently.

- Flag rows that combine unrelated behavior, multiple components, or multiple acceptance paths.
- Flag SR candidates that cannot become separately owned AR work items.
- Mechanical splitting by sentence is not enough; split by behavior, ownership, risk, and verification boundary.
- Cross-component or subsystem ambiguity should be surfaced as USER-INPUT or TEAM-EXPERT rather than guessed.
