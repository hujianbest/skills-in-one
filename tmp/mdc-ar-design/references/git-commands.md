# Git 命令参考

## 查看仓库状态

```bash
git status
```

## 查看未暂存的修改

```bash
git diff
```

## 查看已暂存的修改

```bash
git diff --cached
```

## 查看最近 N 次提交

```bash
git log --oneline -10
```

## 查看某个文件的修改历史

```bash
git log --oneline -10 -- 文件路径
```

## 查看新增文件（未跟踪文件）

```bash
git status --porcelain
```

## 查看两次提交之间的差异

```bash
git diff HEAD~1 HEAD
```

## 获取作者信息

```bash
git config user.name
git config user.email
```

## 获取 AR 编号

1. **优先从 git commit 中获取**：查看最近一次提交的日期和序号
2. **如果无法获取**：使用当天日期 + 00001 作为初始编号