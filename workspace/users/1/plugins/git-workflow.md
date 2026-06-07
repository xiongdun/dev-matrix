# git-workflow

## 描述

Git 工作流自动化插件，规范提交信息和分支命名。

## 功能

- 自动生成 conventional commit 格式的提交信息
- 分支命名规范：`feature/`, `fix/`, `chore/`, `docs/`
- PR 描述模板生成

## 触发条件

- Agent 生成代码补丁后
- 用户请求提交代码时

## 配置

| 选项 | 默认值 | 说明 |
|------|--------|------|
| commit_style | conventional | 提交信息风格 |
| branch_prefix | feature/ | 默认分支前缀 |
| auto_pr | true | 是否自动创建 PR |
