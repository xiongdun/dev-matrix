# github-mcp

## 服务器信息

- **类型**: stdio
- **命令**: npx -y @modelcontextprotocol/server-github
- **描述**: GitHub 仓库操作（issues、PR、文件读写）

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| GITHUB_TOKEN | GitHub Personal Access Token | 是 |
| GITHUB_OWNER | 默认仓库所有者 | 否 |

## 可用工具

| 工具 | 描述 |
|------|------|
| search_repositories | 搜索仓库 |
| create_issue | 创建 Issue |
| create_pull_request | 创建 PR |
| get_file_contents | 读取文件内容 |

## 使用场景

- 代码审查时自动获取 PR diff
- 创建 Issue 跟踪任务
- 读取远程仓库文件进行分析
