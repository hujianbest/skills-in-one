# Dry Run T-NFR-003-no-tools — No External Tool Chain Dependency

- Date: 2026-04-23
- Profile: lightweight
- Purpose: 验证 NFR-003 "不依赖外部 lint / 翻译 / docs 生成工具链；可选工具仅作为 evidence 来源"

## Dry Run Setup

- 被测对象: `features/001-hf-doc-freshness-gate/` 自身
- 当前仓库工具链状态（基线即测试环境）：
  ```bash
  $ ls -la /workspace/.gitignore /workspace/Makefile 2>&1 | head
  -rw-r--r-- 1 ubuntu ubuntu 18 Apr 23 13:53 /workspace/.gitignore
  ls: cannot access '/workspace/Makefile': No such file or directory
  ```
- 仓库**无** Vale / markdownlint / OpenAPI lint / docs site CI / 自动翻译工具
- 仓库**无** package.json / requirements.txt / pyproject.toml / Cargo.toml（纯 prose 仓库）

## Reviewer 派发模拟

reviewer subagent 按 `SKILL.md` Workflow 执行：

1. 读 spec.md / tasks.md / git log → 形成 user-visible change list ✅（不依赖工具链）
2. 按 `references/profile-rubric.md` 激活 lightweight 强制维度（仓库根 README + Conventional Commits）✅（不依赖工具链）
3. 文件系统扫描（`test -f`/`ls`）✅（不依赖工具链）
4. 维度判定：
   - 仓库根 README：cold-read README.md 当前内容 vs user-visible change list（reviewer 直接基于文件内容冷读）✅（不依赖工具链）
   - Conventional Commits：`git log --grep '^docs:'` ✅（git 是 baseline，不算"外部 lint 工具链"）
5. 按 `templates/lightweight-checklist-template.md` 填 verdict ✅（不依赖工具链）
6. 写 evidence 文件 ✅（不依赖工具链）

## 结论

**NFR-003 PASS** ✅

整轮 dogfooding 在仓库**无**任何 docs lint / translation / generation 工具链的状态下完整跑通。reviewer 仅依赖：

- 文件系统命令（`test -f`、`ls`、`cat`）—— Unix baseline，不算"外部工具链"
- `git log` —— git 是 baseline（HF skill pack 的运行环境前提），不算"外部 lint 工具链"
- `python3` / `jq` —— 在 cloud agent 环境为 baseline，但 reviewer 派发实际不依赖（这两个工具仅在 T1..T6 任务的 Verify 段使用）

**反向验证**：本 dogfooding 中**未**使用 / 未要求项目方安装 markdown-lint / spell check / vale / OpenAPI validator / 翻译工具。`SKILL.md` Red Flags 列出的 "误以为强制 lint / 翻译 / docs 生成工具链" 模式被本测试有效证伪。
