# Requirement Rows 评审摘录

Spec review 检查每条核心 row 是否具备 ID、Statement、Acceptance、Priority、Source / Trace Anchor，以及按类型必需的 Component Impact 或 Affected Components。

- Statement 应使用 EARS-style 结构，避免模糊 actor、隐藏 timing 和不可测试措辞。
- Acceptance 应采用 BDD-like Given / When / Then，并可独立判断。
- Source 必须指向 IR / SR / AR / meeting note / owner decision，而不是无记录记忆。
- SR rows 使用 Affected Components；AR / DTS / CHANGE rows 使用 Component Impact。
- 缺业务事实属于 USER-INPUT；措辞 / 结构缺口通常是 LLM-FIXABLE；组件边界决策属于 TEAM-EXPERT。
