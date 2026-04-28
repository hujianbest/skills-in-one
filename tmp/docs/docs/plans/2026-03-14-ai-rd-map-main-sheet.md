# AI辅助研发主地图 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 补全 `AI辅助开发沙盘V2.xlsx` 当前主地图页中与 AI 作业设计相关的核心列，使其成为可执行的 AI 辅助研发地图。

**Architecture:** 采用“保留现有事项结构 + 批量补齐活动级 AI 作业设计”的方式实施。通过脚本直接更新工作簿主地图页，保持用户原始表格结构，同时将 AI 任务、系统措施、人在环职责、风险和价值闭环统一写入对应列。

**Tech Stack:** Python、openpyxl、现有工作簿模板、批量填表脚本

---

### Task 1: 确认目标工作簿与主表结构

**Files:**
- Modify: `C:/Users/h00514071/Desktop/docs/AI辅助开发沙盘V2.xlsx`
- Check: `C:/Users/h00514071/Desktop/docs/build_ai_rd_map.py`

**Step 1: 读取工作簿工作表与表头**

运行脚本读取工作表名称、行列数、前几行内容，确认主地图页为第一张表，且目标列顺序与当前设计一致。

**Step 2: 验证当前已有活动与痛点内容**

检查用户已输入的事项、活动分解、当前痛点是否完整，避免覆盖错误内容。

**Step 3: 确认仅更新主地图页**

实施时只更新当前主工作表，不新增其他辅助表。

### Task 2: 组织主地图页补全内容

**Files:**
- Modify: `C:/Users/h00514071/Desktop/docs/build_ai_rd_map.py`
- Reference: `C:/Users/h00514071/Desktop/docs/docs/plans/2026-03-14-ai-rd-map-design.md`

**Step 1: 为每个事项整理补全字段**

补齐以下字段：
- `执行方式`
- `AI完成活动中的什么任务`
- `AI解决措施`
- `人在活动中完成什么任务`
- `AI执行的潜在问题`
- `优先级`
- `AI解决了哪些痛点`

**Step 2: 保证措施足够具体**

所有 `AI解决措施` 必须写到工具、触发时机、Agent 形态和流程回写层面，例如：
- `在 IDE 中启用 opencode 的 TDD 技能`
- `在 Git MR/PR 门禁中部署 AI 检视 Agent`
- `在 CI/CD 中部署 AI Quality Gate Agent`

**Step 3: 保持人机协同边界**

对所有高风险事项保留人工审批、放行、定版、定责、关闭等关键动作。

### Task 3: 执行工作簿更新

**Files:**
- Modify: `C:/Users/h00514071/Desktop/docs/AI辅助开发沙盘V2.xlsx`

**Step 1: 运行 Python 脚本更新主地图页**

使用 `openpyxl` 读取工作簿，并仅对主地图页进行批量写入。

**Step 2: 保留原有样式与结构**

不要破坏原有表头、合并单元格、行高与列顺序；只清理并重写第 3 行及以下的数据区域。

**Step 3: 保存覆盖原文件**

输出到原始文件路径，便于用户直接查看最终结果。

### Task 4: 验证输出结果

**Files:**
- Check: `C:/Users/h00514071/Desktop/docs/AI辅助开发沙盘V2.xlsx`

**Step 1: 重新读取工作簿抽样检查**

检查工作表名称、总行数和关键行内容，确认补齐列已写入。

**Step 2: 验证典型事项内容**

至少检查以下事项：
- `编码`
- `代码检视`
- `门禁自动化质量防护`

确认其 `AI解决措施` 已达到“可实施”粒度。

**Step 3: 向用户汇报验证边界**

说明已更新主地图页；如果未运行真实业务系统联调或格式人工复核，需要明确说明。
