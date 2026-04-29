# 粒度与拆分评审摘录

Spec review 检查 requirement rows 与 SR AR candidates 是否足够小，能被独立设计、评审、实现和验证。

- 标出混合无关行为、多个组件或多条 acceptance paths 的 rows。
- 标出无法成为独立归属 AR work items 的 SR candidates。
- 只按句子机械拆分不够；应按行为、归属、风险和验证边界拆分。
- 跨组件或子系统歧义应作为 USER-INPUT 或 TEAM-EXPERT 暴露，不要猜。
