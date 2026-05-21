# DevFlow：把 AI Coding 变成可审计工作流

AI Coding 已经不再是一个“能不能写出代码”的问题。

在很多团队里，Agent 已经可以读代码、改代码、补测试、跑命令、解释错误，甚至连续完成一串实现任务。但越往真实工程环境里走，我们越容易发现：让 AI 写代码并不难，难的是让这段工作被团队信任。

一段 AI 参与的开发过程，能不能在新会话里恢复？能不能被独立审查？能不能留下足够证据？能不能说明为什么这样设计？能不能知道现在到底卡在哪个 gate？这些问题，决定了 AI Coding 是一个“个人效率工具”，还是可以进入团队协作链路的工程系统。

DevFlow 试图回答的就是这个问题：如何把 AI Coding 从聊天式协助，变成可恢复、可审查、可交接、可收口的工作流。

## 问题钩子

### 1. AI Coding过程中，我们在抱怨什么

当一个 Agent 写错代码时，团队通常不会只抱怨“模型不够聪明”。真正让人不放心的，往往是过程不可控。

我们会抱怨它改得太快，却说不清为什么这样改；会抱怨它一边修 bug 一边顺手重构，最后范围变大；会抱怨它声称“已经完成”，但测试证据、review 记录、完成标准都不完整；会抱怨换一个新会话之后，前面的上下文像断片一样，只能靠模型从聊天记录里猜。

更深一层的问题是：AI Coding 常常把工程活动压缩成一段对话。需求澄清、设计取舍、实现过程、测试结果、代码审查、完成判断都混在一起。短期看很流畅，长期看很难追踪。

这会带来几个典型风险：

- 状态丢失：下一步依赖聊天记忆，而不是稳定的工程记录。
- 自我证明：同一个 Agent 写完实现，又自己判断质量通过。
- 设计隐身：关键取舍没有落盘，后来的人只能从 diff 里反推。
- 门禁虚化：是否完成取决于一句“已完成”，而不是可回读的证据包。
- 责任混乱：业务范围、架构边界、质量判断都被 Agent 默默代替团队做了。

如果 AI Coding 只服务个人探索，这些问题也许可以忍。但如果它要进入团队研发流程，这些问题就会变成协作成本和质量风险。

### 2. SDD解决了什么，还剩什么

SDD，也就是 Spec-Driven Development，已经向前走了一大步。它提醒我们不要一上来就让 Agent 写代码，而是先把意图写清楚：需求是什么，边界是什么，验收标准是什么，设计方案是什么，测试应该覆盖什么。

这解决了 AI Coding 里一个很关键的问题：从“边聊边做”转向“先定义，再实现”。规格和设计让 Agent 不再只依赖模糊 prompt，也让团队有机会在实现前发现范围、接口、验收标准上的问题。

但 SDD 之后，还剩几个问题没有自然消失。

第一，规格写出来以后，谁来判断它足够好？如果仍然是同一个 Agent 自己写、自己审，那只是把自我证明前移到了 spec 阶段。

第二，设计通过以后，如何保证实现过程按设计推进？实现是否按 TDD 走，测试是否真的有效，代码是否通过独立检视，这些都不是“有 spec”就自动成立。

第三，状态如何恢复？一个团队真实的工作项不是一次 prompt 就结束，它会跨天、跨会话、跨人、跨 review。下一步应该从哪里继续，不能依赖聊天窗口还在。

第四，什么时候可以宣布完成？工程上的完成不是“代码生成完了”，而是需求、设计、实现、测试、review、证据、收尾都满足定义。

所以，SDD 解决了“先想清楚再做”的问题，但还没有完整解决“怎么把这件事作为团队工程流程跑完”的问题。

### 3. 解决思路

DevFlow 的解决思路不是让 Agent 变得更会解释，也不是把 prompt 写得更长，而是把 AI Coding 重新放回工程流程里。

它把一次 AI 参与的开发工作拆成显式阶段：规格、设计、TDD 实现、测试有效性审查、代码检视、完成门禁、收尾。每个阶段都有自己的输入、输出、角色边界和进入条件。

更重要的是，DevFlow 不把聊天当作唯一事实来源。它要求关键状态和证据落到磁盘 artifacts 里。新的会话、新的 Agent、新的 reviewer，都应该能从 `features/<id>/progress.md`、`reviews/`、`evidence/`、`completion.md` 里恢复当前状态，而不是从聊天记忆里猜。

这就是 DevFlow 的核心方向：把 AI Coding 从“能力驱动”变成“证据驱动”，从“聊天协助”变成“可审计工作流”。

## Context：DevFlow 管什么，不管什么

DevFlow 有一个很重要的边界：它只管开发阶段。

它不做产品发现，不替需求负责人决定业务方向；它不做发布流程，不替团队管理上线节奏；它也不是运行时事故响应系统，不负责替 SRE 或值班同学处理生产事件。

DevFlow 的入口，是团队已经接受的 SR、AR、DTS 或 CHANGE。换句话说，工作项已经存在，团队已经决定要处理它。DevFlow 要做的是把这个工作项从需求澄清推进到规格、设计、实现、review、completion gate 和 closeout，并让每一步都有可回读的工程产物。

这种窄边界很重要。AI 工作流最危险的地方之一，是在没有授权的情况下替团队做范围、优先级、架构、接口契约等决策。DevFlow 的立场是：这些决策属于 requirement owner、module architect、dev lead 或开发团队本身。Agent 可以暴露问题、整理选项、记录证据，但不能静默越权。

## Core：DevFlow 如何把流程跑起来

DevFlow 的核心，不是一条口号，而是一组强约束。

### 13 个 canonical nodes

DevFlow 把工作流定义成有限状态机，而不是自由发挥的聊天路径。节点名称必须是 canonical 的，不能写成“下一步继续优化一下”这种自由文本。

典型实现路径是：

```text
using-devflow
  -> devflow-router
  -> devflow-specify
  -> devflow-spec-review
  -> devflow-ar-design
  -> devflow-ar-design-review
  -> devflow-tdd-implementation
  -> devflow-test-review
  -> devflow-code-review
  -> devflow-completion-gate
  -> devflow-finalize
```

如果工作影响组件边界，会插入 `devflow-component-design` 和 `devflow-component-design-review`。如果是 DTS / hotfix，会先进入 `devflow-problem-fix` 做复现、根因和最小安全修复边界。

这套 canonical nodes 的意义，是让“下一步”不再靠 Agent 随口决定。每次推进都要落到一个明确节点，每个节点都有明确职责。

### Artifact-first：磁盘比聊天更可信

DevFlow 的第一原则是 artifact-first。

工作项的当前状态写在 `features/<id>/progress.md`。评审结论写在 `reviews/`。测试、命令、验证记录写在 `evidence/`。完成判断写在 `completion.md`。收尾时，长期资产会推广到 `docs/ar-specs/`、`docs/ar-designs/` 或 `docs/component-design.md`。

这意味着一个新会话不需要“回忆”之前发生了什么。它应该读取 artifacts，恢复当前 profile、stage、pending reviews、blockers 和 next action。

当聊天历史和磁盘 artifacts 冲突时，DevFlow 选择磁盘 artifacts。这不是因为文件永远不会错，而是因为团队工程需要一个可审计、可修正、可引用的事实来源。聊天可以帮助协作，但不应该成为唯一记录。

### Role separation：不允许自我审查

DevFlow 的第二个关键原则是 role separation。

Authoring nodes 负责写产物，例如规格、组件设计、AR 设计、实现代码和测试证据。Review nodes 负责独立审查，例如 spec review、component design review、AR design review、test review、code review。

Reviewer 必须由 `devflow-router` 派发为独立 subagent。它读取被审查 artifacts，返回 verdict、findings 和下一步建议，但不能顺手修改生产代码或测试。

这条规则看起来有点严格，但它解决的是 AI Coding 中最常见的质量幻觉：写作者自己说“我觉得没问题”。在团队流程里，完成质量判断的人和生产产物的人必须分开。

### Hard gates：质量不能靠语气通过

DevFlow 不允许 Agent 用“这个很简单”“我稍后补”“用户说 auto 所以可以跳过”这样的理由绕过 gate。

几个典型 hard gate 是：

- AR 设计没有嵌入 test design，不能进入 TDD 实现。
- TDD 完成后没有 `devflow-test-review` verdict，不能进入 code review。
- 缺少 `devflow-code-review` verdict，不能进入 completion gate。
- completion gate 不通过，不能 finalize。
- SR 的 `requirement-analysis` profile 不能在同一个工作项里跳到实现节点。

这些 gate 的价值不是制造仪式感，而是把团队质量要求结构化。Agent 不能靠更自信的语言通过门禁，只能靠 artifacts 和 evidence 通过。

### Profiles and modes：路径可以轻重不同，底线不能变

DevFlow 不是一条僵硬流程。它有不同 workflow profiles：

- `requirement-analysis`：用于 SR，只做需求分析和候选 AR，不直接实现。
- `standard`：普通 AR / CHANGE 的完整实现路径。
- `component-impact`：当工作影响组件边界、接口、依赖、状态机或新增组件时插入组件设计。
- `hotfix`：用于 DTS，先复现和根因，再最小安全修复。
- `lightweight`：用于低风险小改动，可以压缩文档量，但不跳过 traceability、evidence、review 和 completion。

Profile 由 `devflow-router` 基于 artifacts 和风险信号判断，不由 Agent 随口选择。Profile 可以按风险升级，例如从 `standard` 升到 `component-impact`，但不能为了省事悄悄降级。

Execution Mode 则只有两个：`interactive` 和 `auto`。它们控制的是节点之间是否停下来等人确认，而不是质量标准。

### TDD context pack：实现也要控制上下文边界

在实现阶段，DevFlow 也避免把整段聊天历史塞给实现 Agent。

`devflow-tdd-implementation` 可以派发 fresh implementer subagent，但传入的是 curated Implementer Context Pack：当前任务目标、允许修改的文件、关联 test case、验证命令、必要上下文和输出要求。

实现者返回的状态也必须结构化：`DONE`、`DONE_WITH_CONCERNS`、`NEEDS_CONTEXT` 或 `BLOCKED`。

这样做的目的是让实现过程更可控。Controller 不需要无限膨胀上下文，implementer 也不会因为看见太多历史信息而越界改动。

## Shift：auto 不是跳过流程，而是不暂停

很多人第一次听到 `auto`，会自然理解成“自动一路跑完”。但在 DevFlow 里，`auto` 从来不是“跳过 review”和“跳过 gate”的许可。

`auto` 只意味着：当当前节点产物合格、review verdict 存在、gate 条件满足、下一步唯一明确时，controller 可以继续进入下一个节点，而不必每次都停下来问人。

它不意味着：

- 没有 test design 也能进入 TDD。
- 没有 test review 也能进入 code review。
- 没有 code review 也能进入 completion gate。
- completion evidence 不完整也能 finalize。
- 业务、范围、架构问题可以由 Agent 静默决定。

换句话说，`auto` 改变的是节奏，不改变质量门槛。它让流程更顺，但不让流程变薄。

这也是 DevFlow 和普通“让 Agent 一直干下去”的区别。普通自动化追求不中断，DevFlow 追求在 gate 满足时不中断。

## Takeaway：从聊天变成工程系统

DevFlow 的核心价值，可以用一句话概括：

> 它把 AI Coding 从聊天协助，变成可审计的工程工作流。

这里的“可审计”不是为了流程洁癖，而是为了让 AI 真正进入团队协作。

一个可审计的 AI Coding 工作流，至少应该做到：

- 下一步可以从 artifacts 恢复，而不是从聊天记忆猜。
- 设计、实现、测试、review、completion 各有明确边界。
- 作者不能审查自己的产物。
- Gate 只能由 evidence 通过，不能由话术通过。
- Profile 可以按风险调整，但质量底线不能下降。
- Agent 遇到业务、范围、架构决策时，要暴露问题，而不是替团队拍板。

如果说 prompt engineering 解决的是“怎么让模型更好地回答”，SDD 解决的是“怎么让模型先理解再实现”，那么 DevFlow 关注的是下一层问题：怎么让 AI 参与的软件开发过程，可以被团队恢复、审查、追踪和收口。

AI 会写代码已经不稀奇。接下来真正重要的是：AI 写下的每一步，能不能成为团队工程系统的一部分。

这就是 DevFlow 要做的事。

## 参考阅读

- [DevFlow README](../README.md)
- [DevFlow 使用指南](guides/devflow-usage-guide.md)
- [DevFlow Workflow Architecture](principles/04%20workflow-architecture.md)
- [Artifact Layout](principles/03%20artifact-layout.md)
