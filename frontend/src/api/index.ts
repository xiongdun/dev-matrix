/**
 * @file DevMatrix API 客户端
 * @description 封装后端 API 调用，提供类型安全的请求方法
 * @module api
 *
 * @example
 * ```ts
 * import { api } from './api'
 *
 * const agents = await api.getAgentDetails()
 * await api.mountSkill('agent_1', 'skill_1')
 * ```
 */

const API_BASE = ''

/**
 * 统一的 API 请求函数
 * @template T 响应数据类型
 * @param {string} url - 请求路径
 * @param {RequestInit} [options] - 请求选项
 * @returns {Promise<T>} 解析后的 JSON 数据
 * @throws {Error} 网络错误或 HTTP 错误时抛出
 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), 30000)

  try {
    const response = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
      ...options,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText)
      throw new Error(`API Error ${response.status}: ${errorText}`)
    }

    return response.json() as Promise<T>
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout after 30s')
      }
      throw error
    }
    throw new Error('Unknown network error')
  }
}

/**
 * 带重试的 API 请求
 * @template T 响应数据类型
 * @param {string} url - 请求路径
 * @param {RequestInit} [options] - 请求选项
 * @param {number} [maxRetries=3] - 最大重试次数
 * @returns {Promise<T>} 解析后的 JSON 数据
 */
async function requestWithRetry<T>(
  url: string,
  options?: RequestInit,
  maxRetries: number = 3,
): Promise<T> {
  let lastError: Error | undefined

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await request<T>(url, options)
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error))
      // 不重试客户端错误 (4xx)
      if (lastError.message.includes('API Error 4')) {
        throw lastError
      }
      if (attempt < maxRetries) {
        const delay = Math.min(1000 * 2 ** attempt, 10000)
        await new Promise((resolve) => setTimeout(resolve, delay))
      }
    }
  }

  throw lastError ?? new Error('Request failed after retries')
}

// ==================== API 导出 ====================

export const api = {
  /** 健康检查 */
  getHealth() {
    return requestWithRetry<{ status: string }>('/health')
  },

  /** 获取需求列表 */
  getRequirements() {
    return requestWithRetry<Array<{ id: string; title: string; status: string }>>('/requirements/')
  },

  /** 创建需求 */
  createRequirement(data: { requirement_raw_input: string }) {
    return requestWithRetry<{ id: string }>('/requirements/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /** 获取审批状态 */
  getApprovals(projectId: string) {
    return requestWithRetry<{ state: string; pending: boolean }>(`/approvals/${projectId}/state`)
  },

  /** 提交审批 */
  submitApproval(projectId: string, status: 'approved' | 'rejected', comment?: string) {
    const params = new URLSearchParams({ status })
    if (comment) params.append('comment', comment)
    return requestWithRetry<{ success: boolean }>(`/approvals/${projectId}?${params.toString()}`, {
      method: 'POST',
    })
  },

  /** 启动工作流 */
  startWorkflow(projectId: string, data: { repo_path: string; raw_input: string }) {
    return requestWithRetry<{ workflow_id: string }>(`/workflow/${projectId}/start`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /** 获取 Agent 详情 */
  getAgentDetails() {
    return requestWithRetry<{ agents: Array<{ name: string; description: string; status: string; skills: string[] }> }>('/registry/agents/detail')
  },

  /** 获取 Skill 列表 */
  getSkills() {
    return requestWithRetry<{ skills: Array<{ name: string; description: string; used_by: string[] }> }>('/registry/skills')
  },

  /** 挂载 Skill */
  mountSkill(agentName: string, skillName: string) {
    return requestWithRetry<{ success: boolean }>(`/registry/agents/${agentName}/skills/${skillName}`, {
      method: 'POST',
    })
  },

  /** 卸载 Skill */
  unmountSkill(agentName: string, skillName: string) {
    return requestWithRetry<{ success: boolean }>(`/registry/agents/${agentName}/skills/${skillName}`, {
      method: 'DELETE',
    })
  },

  /** 上传自定义 Skill */
  uploadSkill(payload: { name: string; description: string; code: string; config?: Record<string, unknown> }) {
    return requestWithRetry<{ success: boolean; name: string; description: string }>('/registry/skills/upload', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /** 获取工作流列表 */
  getWorkflows() {
    return requestWithRetry<{ workflows: Array<{ id: number; name: string; description: string; version: string; status: string; created_at: string; updated_at: string }> }>('/workflow-config/')
  },

  /** 获取单个工作流 */
  getWorkflow(id: number) {
    return requestWithRetry<{ id: number; name: string; description: string; version: string; flow_json: string; status: string }>('/workflow-config/' + id)
  },

  /** 创建工作流 */
  createWorkflow(data: { name: string; description?: string }) {
    return requestWithRetry<{ id: number; name: string }>('/workflow-config/', { method: 'POST', body: JSON.stringify(data) })
  },

  /** 保存工作流 */
  saveWorkflow(id: number, data: { name?: string; description?: string; flow_json?: string; status?: string }) {
    return requestWithRetry<{ id: number; name: string }>('/workflow-config/' + id, { method: 'PUT', body: JSON.stringify(data) })
  },

  /** 删除工作流 */
  deleteWorkflow(id: number) {
    return requestWithRetry<{ success: boolean }>('/workflow-config/' + id, { method: 'DELETE' })
  },

  getWorkbenchTasks(role: string) {
    return requestWithRetry<{tasks: Array<{id: number; project_id: string; stage_id: string; stage_name: string; agent_role: string; status: string; output_json: string; feedback: string | null; arrived_at: string; processed_at: string | null}>}>('/workbench/tasks?role=' + role)
  },
  getWorkbenchTask(taskId: number) {
    return requestWithRetry<{id: number; project_id: string; stage_id: string; stage_name: string; agent_role: string; status: string; output_json: string; feedback: string | null; arrived_at: string; processed_at: string | null}>('/workbench/tasks/' + taskId)
  },
  approveWorkbenchTask(taskId: number) {
    return requestWithRetry<{success: boolean; task: any}>('/workbench/tasks/' + taskId + '/approve', { method: 'POST' })
  },
  rejectWorkbenchTask(taskId: number, comment?: string) {
    return requestWithRetry<{success: boolean; task: any}>('/workbench/tasks/' + taskId + '/reject', { method: 'POST', body: JSON.stringify({ comment }) })
  },
  retryWorkbenchTask(taskId: number, feedback?: string) {
    return requestWithRetry<{success: boolean; task: any}>('/workbench/tasks/' + taskId + '/retry', { method: 'POST', body: JSON.stringify({ feedback }) })
  },
  getWorkbenchStats(role: string) {
    return requestWithRetry<{pending: number; completed: number; rejected: number}>('/workbench/stats?role=' + role)
  },

  subscribeToEvents(role?: string, onEvent?: (data: any) => void): () => void {
    const params = role ? `?role=${role}` : ''
    const eventSource = new EventSource(`/events/stream${params}`)

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onEvent?.(data)
      } catch {}
    }

    eventSource.onerror = () => {
      eventSource.close()
    }

    return () => eventSource.close()
  },
}
