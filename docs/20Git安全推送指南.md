# Git安全推送指南

## 概述

本指南确保您的代码只推送到您的fork仓库 (hangeaiagent/cooragent)，而不会意外推送到原始仓库 (LeapLabTHU/cooragent)。

## 当前安全配置

### ✅ 已配置的安全措施

1. **远程仓库配置**
   ```bash
   origin: https://github.com/hangeaiagent/cooragent.git
   # 没有配置upstream，避免意外推送到原始仓库
   ```

2. **Push默认行为**
   ```bash
   push.default: simple
   # 只推送当前分支到同名的上游分支
   ```

3. **安全别名**
   ```bash
   git pushfork    # 等同于 git push origin main
   git statusfork  # 等同于 git status -b
   ```

## 🛡️ 安全操作流程

### 日常开发流程

```bash
# 1. 检查状态和分支
git statusfork

# 2. 添加更改
git add <files>

# 3. 提交更改
git commit -m "your commit message"

# 4. 安全推送到您的fork
git pushfork
# 或者明确指定
git push origin main
```

### 🚨 危险命令避免列表

```bash
# ❌ 避免使用的命令
git push --all              # 可能推送所有分支
git push --mirror           # 完全镜像推送
git push upstream           # 如果配置了upstream会推送到原始仓库
git push --force            # 强制推送可能覆盖其他人的工作

# ✅ 安全的替代方案
git push origin main        # 明确指定推送目标
git push origin --force-with-lease  # 更安全的强制推送
```

## 🔍 定期安全检查

### 每月检查清单

```bash
# 1. 检查远程仓库配置
git remote -v

# 2. 确认应该只有origin指向您的fork
# origin  https://github.com/hangeaiagent/cooragent.git (fetch)
# origin  https://github.com/hangeaiagent/cooragent.git (push)

# 3. 检查分支跟踪
git branch -vv

# 4. 确认push配置
git config --get push.default
# 应该返回: simple
```

## 🔧 如果需要从原始仓库获取更新

如果您需要从原始仓库获取最新更改，请按以下**安全**流程：

### 方法1：临时添加upstream（推荐）

```bash
# 1. 临时添加原始仓库
git remote add upstream https://github.com/LeapLabTHU/cooragent.git

# 2. 获取原始仓库的更新
git fetch upstream

# 3. 合并到您的分支
git merge upstream/main

# 4. 推送到您的fork
git push origin main

# 5. 删除upstream远程仓库（安全措施）
git remote remove upstream
```

### 方法2：手动下载（最安全）

```bash
# 1. 手动下载原始仓库的ZIP
# 2. 比较差异并手动合并需要的更改
# 3. 正常提交到您的fork
```

## ⚠️ 重要注意事项

### 1. 远程仓库管理

- **永远不要**设置permanent upstream指向原始仓库
- 如果需要upstream，用完立即删除
- 定期检查 `git remote -v` 确保配置正确

### 2. 分支管理

```bash
# 创建新分支时明确指定origin
git checkout -b new-feature
git push -u origin new-feature  # 明确设置上游分支

# 避免意外跟踪错误的远程分支
git branch --set-upstream-to=origin/main  # 明确设置跟踪
```

### 3. 协作注意事项

```bash
# 如果有其他贡献者，确保他们也遵循相同的安全规则
# 在README中说明推送策略
```

## 🚨 意外推送到原始仓库的补救措施

如果意外推送到了原始仓库：

1. **立即联系原始仓库维护者**
2. **说明情况并请求删除错误的推送**
3. **检查并修复本地Git配置**
4. **遵循本指南重新配置安全措施**

## 🔒 额外安全建议

### 1. Git钩子保护

创建pre-push钩子防止意外推送：

```bash
# .git/hooks/pre-push
#!/bin/sh
remote="$1"
url="$2"

if [ "$url" != "https://github.com/hangeaiagent/cooragent.git" ]; then
    echo "错误: 尝试推送到非fork仓库: $url"
    echo "只允许推送到: https://github.com/hangeaiagent/cooragent.git"
    exit 1
fi
```

### 2. 配置文件备份

定期备份Git配置：

```bash
# 导出配置
git config --list > git-config-backup.txt

# 特别关注这些配置
git config --get remote.origin.url
git config --get push.default
```

## 📋 快速参考卡

### 安全命令速查

| 操作 | 安全命令 | 说明 |
|------|----------|------|
| 检查状态 | `git statusfork` | 查看分支和状态 |
| 推送代码 | `git pushfork` | 安全推送到fork |
| 检查远程 | `git remote -v` | 确认远程仓库配置 |
| 检查分支 | `git branch -vv` | 查看分支跟踪关系 |
| 明确推送 | `git push origin main` | 最安全的推送方式 |

### 紧急联系信息

- **原始仓库**: https://github.com/LeapLabTHU/cooragent
- **您的Fork**: https://github.com/hangeaiagent/cooragent
- **问题报告**: 如有配置问题，请查看此文档或联系团队

---

**最后更新**: 2025-07-27  
**版本**: v1.0  
**适用范围**: hangeaiagent/cooragent fork仓库 