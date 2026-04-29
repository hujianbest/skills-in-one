# NFR Quality Attribute Scenario 评审摘录

Spec review 检查 embedded NFRs 是否写成包含 stimulus source、stimulus、environment、response、response measure 的 quality attribute scenarios。

- Response Measure 需要阈值或可观察的 pass/fail criterion。
- Acceptance criteria 必须匹配 QAS，不得引入另一个 metric。
- 把 latency、memory、concurrency、availability、safety、security 混在一条 row 的 NFR 拆开。
- 缺 thresholds 或 operating conditions 属于 USER-INPUT / TEAM-EXPERT，不由 reviewer 猜测。
