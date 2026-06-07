# docker-builder

## 描述

Docker 镜像构建和管理插件。

## 功能

- 自动生成 Dockerfile（基于项目类型检测）
- 构建镜像并运行容器
- 多阶段构建优化
- 镜像大小分析

## 触发条件

- 用户请求容器化部署时
- 检测到项目缺少 Dockerfile 时

## 命令

| 命令 | 说明 |
|------|------|
| `build` | 构建镜像 |
| `run` | 运行容器 |
| `stop` | 停止容器 |
| `logs` | 查看日志 |

## 约束

- 不要修改已有的 Dockerfile
- 构建前先检查 .dockerignore
