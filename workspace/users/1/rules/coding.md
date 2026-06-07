# 编码规则

## 禁止

- 不要使用 `any` 类型（TypeScript/Python）
- 不要删除已有测试
- 不要修改 `.env` 文件
- 不要硬编码密钥或 Token
- 不要在循环中执行数据库查询（N+1 问题）

## 必须

- 所有 API 端点必须有权限检查（`get_current_user`）
- 数据库操作必须在 `try/except` 中
- 新增字段必须有默认值
- 函数必须有 type hints
- 公共函数必须有 docstring

## 偏好

- 优先使用标准库而非第三方依赖
- 错误信息要包含足够的上下文
- 日志用 logger，不要用 print
