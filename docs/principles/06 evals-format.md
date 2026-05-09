# DevFlow `evals/` 格式

- 定位：定义 DevFlow 高风险 skill 的 `evals/` 目录的统一格式与运行约定。
- 关联：
  - 最高原则：`docs/principles/00 soul.md`
  - Skill 写作原则：`docs/principles/02 skill-anatomy.md`（其中 `## Supporting Files / evals/` 节列出了高风险节点应至少覆盖的边界）

## 为什么有 evals

DevFlow skill 是 LLM 在运行时执行的工程纪律。它的 hard gates、profile 限制、reviewer 角色边界、评审恢复语义不能"看代码就知道是否被遵守"——必须通过**场景化的 misuse 用例**验证 skill 真的能拒绝它声明要拒绝的事情。

`evals/` 不是单元测试，也不是 CI 中能自动跑过的断言。它是：

- **回归用的场景目录**：当 skill 修订后，作者 / reviewer 用这些场景手工或半自动地确认 skill 仍然拒绝/允许它应该拒绝/允许的事情。
- **新贡献者的 contract 清单**：阅读 `evals.json` 比通读全文 SKILL 更快理解"这个 skill 真正在防什么"。
- **review 的硬证据**：当一个 PR 修改了 skill 的 hard gate / profile 规则 / 工作流，PR review 必须确认对应 eval 场景仍然成立或者已经被有意更新。

## 适用范围

`evals/` 不是 DevFlow 所有 skill 的强制要求。当前要求的高风险 skill：

| Skill | 为什么是高风险 |
|---|---|
| `devflow-router` | 决定整个工作流的下一步；错路由 / 静默降 profile / 跨子街区切换都会让其它 skill 全部失效 |
| `devflow-tdd-implementation` | 是 controller 主循环；缺测试设计就 TDD、多 active task、自审跳过 test-checker 都会污染 evidence |
| `devflow-test-checker` | reviewer 越权（补测试 / 改生产代码）会让 review 体系失去意义 |
| `devflow-completion-gate` | DoD 一旦被绕过，整个 work item 就被假装完成 |

未来增加 `devflow-ar-design` / `devflow-code-review` / `devflow-problem-fix` 的 evals 时，遵循同一格式。

## 目录结构

```
skills/devflow-<name>/evals/
  README.md           # 必需。说明本 skill 的 eval 集合如何使用。
  evals.json          # 必需。本 skill 的全部场景目录。
  fixtures/           # 必需。场景引用的最小工件快照。
    <fixture-id>/
      progress.md
      requirement.md
      ar-design-draft.md
      reviews/
      evidence/
      ...
```

`fixtures/` 下每个子目录对应一个 work item 的最小切片，**不是**完整 work item。只放本场景判定下一步所需的最少文件，缺失的可选文件默认表示「不存在」。

## `evals.json` 字段契约

`evals.json` 是一个 JSON 对象，顶层结构：

```json
{
  "skill": "devflow-<name>",
  "version": "1.0.0",
  "purpose": "<one-line summary of what this eval set protects>",
  "scenarios": [ <Scenario>, ... ]
}
```

### `Scenario`

| 字段 | 必需 | 类型 | 说明 |
|---|---|---|---|
| `id` | 是 | string | 稳定 id，`<skill-prefix>-EV-<NNN>`，例如 `router-EV-001` |
| `name` | 是 | string | 一行场景名 |
| `category` | 是 | string | 见下方 Category 表 |
| `severity` | 是 | string | `critical` / `high` / `medium` |
| `setup` | 是 | object | `fixture` 路径 + `progress` overrides |
| `input` | 是 | object | 用户请求 / 上游 handoff |
| `must_do` | 是 | string[] | skill 必须做的事（用于 verdict） |
| `must_not_do` | 是 | string[] | skill 必须不做的事 |
| `expected_handoff` | 是 | object | 期望的结构化 handoff 字段子集 |
| `verification` | 是 | string[] | 如何检查（读哪个字段 / 哪个工件 / 哪行） |
| `notes` | 否 | string | 额外解释或链接到 SKILL 章节 |

`setup.fixture` 是 `evals/fixtures/<id>/` 下的相对目录名。`setup.progress` 可以以 key/value 覆盖 fixture 中 `progress.md` 的字段，便于一个 fixture 衍生多个场景。

`input` 至少含：
- `user_request`：用户的自然语言请求
- `upstream_handoff`（可选）：来自上一个 skill 的结构化 handoff 块
- `artifacts_changed_since_last_run`（可选）：自上一轮以来的工件变化列表

`expected_handoff` 至少含：
- `verdict` 或 `result`（如适用）
- `next_action_or_recommended_skill`（必须是 canonical DevFlow 节点）
- `reroute_via_router`（boolean）
- `blockers` 关键字（如适用）

`verification` 是一个有序检查列表，每条要么是「读 `<file>` 第 N 行 / 第 X 节」，要么是「在 handoff 中确认 `<field> == <value>`」。

### Category 取值

| Category | 含义 | 典型 skill |
|---|---|---|
| `wrong-node-routing` | 把错误的 canonical 节点当下一步 | router / using-devflow |
| `profile-discipline` | 静默升级 / 降级 / 跨子街区切换 | router |
| `evidence-missing` | 缺上游 review record / fresh evidence 仍尝试推进 | router / completion-gate |
| `gate-skipped` | 跳过 test-checker / code-review / completion-gate | router / tdd-implementation / completion-gate |
| `reviewer-overreach` | reviewer 改工件 / 多候选下一步 | test-checker / code-review / spec-review |
| `self-verification` | 实现节点自宣完成 / 自审 | tdd-implementation / completion-gate |
| `subagent-context-discipline` | implementer subagent 收到完整聊天历史而非 Context Pack | tdd-implementation |
| `auto-mode-misuse` | 把 `auto` 解读成跳过 review / approval | router / completion-gate |
| `boundary-drift` | 实现 / 设计绕过 SOA / 组件边界但未升级 profile | tdd-implementation / code-review |
| `template-violation` | 工件缺必需章节 / 输出非 canonical 字段 | 任意 |

每个 scenario 必须落到一个 category，便于按维度统计覆盖率。

## 运行约定

### 手工运行

1. 把目标 fixture 复制到一个临时 work item 目录（例如 `/tmp/devflow-eval/AR99999-eval/`）。
2. 启动一个**新的 OpenCode 会话**（避免聊天记忆污染），把 `setup.input.user_request` 作为唯一输入发出去。
3. 让 agent 按 DevFlow 自然推进，**不**给提示。
4. 收集 agent 的 handoff 与对工件的所有写入。
5. 按 `verification` 列表逐条对照 `must_do` / `must_not_do` / `expected_handoff`。
6. 任一项不满足 → eval `failed`，需要修复 skill（不是修改 eval）。

### 半自动运行（可选）

将来可以写一个简单的 harness：把每个 scenario 的 fixture + input 喂给 OpenCode CLI 的 headless 模式，收集 handoff，按 `verification` 比对。harness 不是 v1.0 的强制要求，但 `evals.json` 字段已经按可程序化的形式设计。

### 失败处理

- `severity = critical` 失败 → release blocker；不修好不允许打 tag。
- `severity = high` 失败 → 必须在 PR 中明确说明并写一个跟踪 issue。
- `severity = medium` 失败 → 视情况（可能是 SKILL 收紧或 eval 老旧）。

### 不允许

- 不允许通过修改 eval 来"绕过"失败。eval 是 skill contract 的固化；如果 contract 真的需要变，先改 SKILL，再同步改 eval，并在 PR 描述里写清楚理由。
- 不允许把 production code 或 production fixture 当 eval fixture。fixture 必须是可读、最小、与具体团队代码无关的合成工件。

## 维护规则

- 每次修改一个高风险 skill 的 hard gate / profile 规则 / 工作流关键步骤，**必须**审查对应 `evals.json` 是否需要新增或更新场景，并在 PR 描述里说明。
- 每个高风险 skill 的 `evals.json` 至少 6 个场景，覆盖至少 3 个不同 category。
- 新增 skill 进入"高风险"集合时，先在 `02 skill-anatomy.md` 的「高风险 devflow skill 应至少覆盖」表中加它，再补 `evals/` 目录。
