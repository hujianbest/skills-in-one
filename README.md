# Skill Steward

*A skill for curating, syncing, indexing, and recommending external skill repositories.*

`Skill Steward` 是一个给 Agent 用的 skill 管家，适合已经收藏了很多 skills 仓库、但越来越难管理的人。它会读取 `REPO_LSIT.md` 中的仓库清单，把这些仓库统一 clone 到工作区外，整理成可搜索的本地 catalog，并在你描述任务时推荐更合适的 skill。

## Why

如果你已经遇到下面这些问题，这个项目就是为你准备的：

- 收藏太多 skill 仓库，记不住每个仓库能做什么
- 做同一类事情时，总要在多个仓库里来回翻
- 想批量 clone 或 update，但不想每次手写一堆 git 命令
- 想在描述任务时，直接得到一组相关 skill 推荐

## Highlights

- 从 `REPO_LSIT.md` 读取仓库列表
- 把外部 skills 仓库统一存放到工作区外
- 只在你明确要求时执行同步或更新
- 扫描 `SKILL.md`、`AGENTS.md` 和必要的 `README`
- 生成本地 catalog，并按任务关键词推荐 skill

## Preview

这里适合放一张截图或一个短 GIF，展示：

- `sync` 后的仓库整理效果
- `index` 生成的 catalog 摘要
- `recommend` 输出的推荐结果

> Preview placeholder: add a screenshot or terminal GIF here later.

## Install

### 依赖

- Python 3.10+
- Git

### 目录位置

这个仓库的源码放在 `skills/skill-steward`。如果你要把它作为 Cursor skill 使用，建议把这个目录复制或链接到以下任一位置：

```text
.cursor/skills/skill-steward
```

或：

```text
~/.cursor/skills/skill-steward
```

如果你把它作为项目 skill 使用，默认配置会更顺手，因为 `REPO_LSIT.md` 通常就在项目根目录。

## Quick Start

### 1. 准备仓库清单

`REPO_LSIT.md` 使用 Markdown 表格格式：

```markdown
| skill-repo        | link                                 |
|-------------------|--------------------------------------|
| example-skills    | https://github.com/example/skills    |
| another-collection| https://github.com/acme/agent-skills |
```

### 2. 查看状态

在源码仓库中直接运行：

```bash
python "skills/skill-steward/scripts/skill_manager.py" status
```

如果已经安装成项目 skill：

```bash
python ".cursor/skills/skill-steward/scripts/skill_manager.py" status
```

### 3. 同步仓库

```bash
python "skills/skill-steward/scripts/skill_manager.py" sync
```

### 4. 生成索引

```bash
python "skills/skill-steward/scripts/skill_manager.py" index
```

### 5. 推荐 skill

```bash
python "skills/skill-steward/scripts/skill_manager.py" recommend --query "ppt corporate presentation deck"
```

`recommend` 当前更适合英文关键词，所以当用户是中文描述时，建议先提炼成 3 到 6 个简短英文词组再查询。

## Commands

| Command | What it does |
|--------|---------------|
| `status` | 查看当前同步状态和 catalog 是否存在 |
| `sync` | clone 缺失仓库，或 pull 已有仓库 |
| `index` | 扫描本地仓库并生成 catalog |
| `recommend --query "..."` | 根据任务关键词推荐 skill |

## Config

源码仓库中的默认配置文件是 `skills/skill-steward/config.json`：

```json
{
  "repo_list_path": "REPO_LSIT.md",
  "clone_root": "~/.cursor/managed-skill-repos/repos",
  "state_root": "~/.cursor/managed-skill-repos/state",
  "scan_files": ["SKILL.md", "AGENTS.md"],
  "include_root_readme": true,
  "recommend_top_k": 6,
  "max_file_bytes": 20000
}
```

关键字段：

- `repo_list_path`: 仓库清单文件路径
- `clone_root`: 外部仓库克隆目录
- `state_root`: catalog 输出目录
- `scan_files`: 扫描哪些文件作为 skill 定义入口
- `recommend_top_k`: 默认返回多少条推荐结果

## Output

索引生成后，会在 `state_root` 下写出两个文件：

- `skill-catalog.json`
- `skill-catalog.md`

## Repo Layout

```text
README.md
REPO_LSIT.md
skills/
  skill-steward/
    SKILL.md
    config.json
    reference.md
    examples.md
    scripts/
      skill_manager.py
```

## Usage

安装好以后，可以直接让 agent 用自然语言调用这套能力，例如：

```text
根据 REPO_LSIT.md，把我的 skill 仓库都 clone 下来，并更新已有仓库。
```

```text
我刚改了 REPO_LSIT.md，重新整理一下本地 skill 目录并更新索引。
```

```text
我想做一份偏华为风格的企业汇报 PPT，帮我推荐合适的 skill。
```

```text
我想把一个复杂任务拆给 agent 长时间执行，推荐几个合适的 skill。
```

## Roadmap

- 给 catalog 增加标签和分类
- 引入更强的中文查询映射
- 增加仓库健康状态检查
- 支持按主题输出 curated collections
