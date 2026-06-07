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

import { useErrorHandler } from '../composables/useErrorHandler'

const API_BASE = '/api'

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
  const { handleApiError } = useErrorHandler()

  try {
    const { headers: customHeaders, ...restOptions } = options || {}

    // 添加 Token
    const authHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...customHeaders,
    }
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token')
      if (token) {
        authHeaders['Authorization'] = `Bearer ${token}`
      }
    }

    const response = await fetch(`${API_BASE}${url}`, {
      headers: authHeaders,
      signal: controller.signal,
      ...restOptions,
    })

    clearTimeout(timeoutId)

    if (response.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      throw new Error('Session expired, please login again')
    }

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText)
      const error = new Error(`API Error ${response.status}: ${errorText}`)
      // 显示友好错误提示
      const friendlyMessage = handleApiError(error)
      useErrorHandler().showError(friendlyMessage)
      throw error
    }

    const contentType = response.headers.get('content-type') || ''
    if (!contentType.includes('application/json')) {
      const text = await response.text()
      throw new Error(`API Error ${response.status}: Expected JSON but got ${contentType}. Response: ${text.slice(0, 200)}`)
    }

    return response.json() as Promise<T>
  } catch (error) {
    clearTimeout(timeoutId)
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        const msg = 'Request timeout after 30s'
        useErrorHandler().showError('请求超时，请检查网络连接后重试')
        throw new Error(msg)
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
  /** 通用 GET 请求 */
  get<T>(url: string, options?: RequestInit) {
    return requestWithRetry<T>(url, { ...options, method: 'GET' })
  },

  /** 通用 POST 请求 */
  post<T>(url: string, body?: any, options?: RequestInit) {
    return requestWithRetry<T>(url, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  },

  /** 通用 PUT 请求 */
  put<T>(url: string, body?: any, options?: RequestInit) {
    return requestWithRetry<T>(url, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  },

  /** 通用 DELETE 请求 */
  delete<T>(url: string, options?: RequestInit) {
    return requestWithRetry<T>(url, { ...options, method: 'DELETE' })
  },

  /** 健康检查 */
  getHealth() {
    return requestWithRetry<{ status: string }>('/health')
  },

  /** 获取需求列表 */
  getRequirements() {
    return requestWithRetry<Array<{ id: string; title: string; status: string }>>('/requirements')
  },

  /** 创建需求 */
  createRequirement(data: { requirement_raw_input: string }) {
    return requestWithRetry<{ id: string }>('/requirements', {
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

  /** 启动工作流（统一入口，优先 Temporal，降级 Pipeline） */
  startWorkflow(projectId: string, data: { repo_path: string; raw_input: string; flow_json?: string; template_id?: number }) {
    return requestWithRetry<{ project_id: string; status: string; engine: string; workflow_id: string }>(`/workflow/${projectId}/start`, {
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
    return requestWithRetry<{ workflows: Array<{ id: number; name: string; description: string; version: string; status: string; is_template: boolean; category: string | null; created_at: string; updated_at: string }> }>('/workflow-config')
  },

  /** 获取工作流模板列表 */
  getWorkflowTemplates() {
    return requestWithRetry<{ templates: Array<{ id: number; name: string; description: string; version: string; status: string; is_template: boolean; category: string | null; flow_json: string }> }>('/workflow-config/templates')
  },

  /** 获取单个工作流 */
  getWorkflow(id: number) {
    return requestWithRetry<{ id: number; name: string; description: string; version: string; flow_json: string; status: string; is_template: boolean; category: string | null }>(`/workflow-config/${id}`)
  },

  /** 创建工作流 */
  createWorkflow(data: { name: string; description?: string; flow_json?: string }) {
    return requestWithRetry<{ id: number; name: string }>('/workflow-config', { method: 'POST', body: JSON.stringify(data) })
  },

  /** 从模板创建实例（自动启动工作流） */
  instantiateTemplate(configId: number, projectId: string, context?: Record<string, unknown>) {
    return requestWithRetry<{ id: number; instance_id: string; project_id: string; current_state: string; participants: string[]; artifacts: any[]; status: string }>(`/workflow-config/${configId}/instantiate`, { method: 'POST', body: JSON.stringify({ project_id: projectId, context: context || {} }) })
  },

  /** 保存工作流 */
  saveWorkflow(id: number, data: { name?: string; description?: string; flow_json?: string; status?: string }) {
    return requestWithRetry<{ id: number; name: string }>(`/workflow-config/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  /** 删除工作流 */
  deleteWorkflow(id: number) {
    return requestWithRetry<{ success: boolean }>(`/workflow-config/${id}`, { method: 'DELETE' })
  },

  /** 获取工作流实例列表 */
  getWorkflowInstances(status?: string) {
    const params = status ? `?status=${status}` : ''
    return requestWithRetry<{ instances: Array<{ id: number; instance_id: string; template_id: number | null; project_id: string; current_state: string; participants: string[]; artifacts: any[]; status: string; started_at: string | null; completed_at: string | null }> }>('/workflow-instances' + params)
  },

  /** 按 project_id 获取工作流实例 */
  getWorkflowInstanceByProject(projectId: string) {
    return requestWithRetry<{ id: number; instance_id: string; template_id: number | null; project_id: string; current_state: string; participants: string[]; artifacts: any[]; status: string }>('/workflow-instances/by-project/' + projectId)
  },

  /** 获取单个工作流实例 */
  getWorkflowInstance(instanceId: string) {
    return requestWithRetry<{ id: number; instance_id: string; template_id: number | null; project_id: string; current_state: string; participants: string[]; artifacts: any[]; status: string }>(`/workflow-instances/${instanceId}`)
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

  /** 获取任务对话历史 */
  getTaskChatHistory(taskId: number) {
    return requestWithRetry<{messages: Array<{id: number; task_id: number; role: string; content: string; tool_calls: string | null; tool_results: string | null; created_at: string}>}>('/workbench/tasks/' + taskId + '/chat')
  },

  /** 发送任务对话消息（不重试，超时 5 分钟） */
  sendTaskChatMessage(taskId: number, message: string, model?: string, sdk?: string) {
    const token = localStorage.getItem('token')
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 分钟超时

    return fetch(`${API_BASE}/workbench/tasks/` + taskId + '/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message, model, sdk }),
      signal: controller.signal,
    }).then(async (resp) => {
      clearTimeout(timeoutId)
      if (!resp.ok) {
        const text = await resp.text()
        throw new Error(`API Error ${resp.status}: ${text}`)
      }
      return resp.json() as Promise<{
        message: {id: number; task_id: number; role: string; content: string; tool_calls: string | null; tool_results: string | null; created_at: string}
        tool_calls: Array<{name: string; input: Record<string, unknown>; result?: Record<string, unknown>}> | null
      }>
    }).catch((err) => {
      clearTimeout(timeoutId)
      throw err
    })
  },

  /** 获取可用 Agent SDK 列表 */
  getAvailableSDKs() {
    return requestWithRetry<{ sdks: Array<{ id: string; name: string; description: string; available: boolean }> }>('/workbench/sdks')
  },

  /** 获取可用 LLM 模型列表 */
  getAvailableModels() {
    return requestWithRetry<{ models: Array<{ id: string; name: string; provider: string }> }>('/workbench/models')
  },

  // ==================== 项目管理 API ====================

  /** 获取项目列表 */
  getProjects(params?: { page?: number; page_size?: number; status?: string; priority?: string; keyword?: string; sort_by?: string; sort_order?: string }) {
    const query = new URLSearchParams()
    if (params?.page) query.append('page', String(params.page))
    if (params?.page_size) query.append('page_size', String(params.page_size))
    if (params?.status) query.append('status', params.status)
    if (params?.priority) query.append('priority', params.priority)
    if (params?.keyword) query.append('keyword', params.keyword)
    if (params?.sort_by) query.append('sort_by', params.sort_by)
    if (params?.sort_order) query.append('sort_order', params.sort_order)
    return requestWithRetry<{ items: Array<{ id: number; name: string; description: string; owner: string; priority: string; status: string; progress: number; start_date: string | null; end_date: string | null; created_at: string; updated_at: string }>; total: number; page: number; page_size: number }>('/projects?' + query.toString())
  },

  /** 创建项目 */
  createProject(data: { name: string; description?: string; owner?: string; priority?: string; status?: string; progress?: number; start_date?: string | null; end_date?: string | null }) {
    return requestWithRetry<{ id: number; name: string; description: string; owner: string; priority: string; status: string; progress: number; start_date: string | null; end_date: string | null; created_at: string; updated_at: string }>('/projects', { method: 'POST', body: JSON.stringify(data) })
  },

  /** 获取项目详情 */
  getProject(id: number) {
    return requestWithRetry<{ id: number; name: string; description: string; owner: string; priority: string; status: string; progress: number; start_date: string | null; end_date: string | null; created_at: string; updated_at: string }>(`/projects/${id}`)
  },

  /** 更新项目 */
  updateProject(id: number, data: Partial<{ name: string; description: string; owner: string; priority: string; status: string; progress: number; start_date: string | null; end_date: string | null }>) {
    return requestWithRetry<{ id: number; name: string; description: string; owner: string; priority: string; status: string; progress: number; start_date: string | null; end_date: string | null; created_at: string; updated_at: string }>(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  /** 删除项目 */
  deleteProject(id: number) {
    return requestWithRetry<void>(`/projects/${id}`, { method: 'DELETE' })
  },

  // ==================== 系统设置 API ====================

  /** 获取所有配置 */
  getSettings(category?: string) {
    const params = category ? '?category=' + category : ''
    return requestWithRetry<{ configs: Array<{ key: string; value: string; category: string; description: string | null; is_sensitive: boolean; updated_at: string | null }> }>('/settings' + params)
  },

  /** 获取配置分类列表 */
  getSettingCategories() {
    return requestWithRetry<{ categories: string[] }>('/settings/categories')
  },

  /** 获取单个配置 */
  getSetting(key: string) {
    return requestWithRetry<{ key: string; value: string; category: string; description: string | null; is_sensitive: boolean; updated_at: string | null }>(`/settings/${key}`)
  },

  /** 批量更新配置 */
  updateSettings(configs: Record<string, string>) {
    return requestWithRetry<{ configs: Array<{ key: string; value: string; category: string; description: string | null; is_sensitive: boolean; updated_at: string | null }> }>('/settings', {
      method: 'PUT',
      body: JSON.stringify({ configs }),
    })
  },

  /** 初始化默认配置 */
  initSettings() {
    return requestWithRetry<{ status: string; message: string }>('/settings/init', { method: 'POST' })
  },

  // ==================== 定时任务 API ====================

  /** 获取定时任务列表 */
  getScheduledTasks() {
    return requestWithRetry<{ tasks: Array<{ id: number; name: string; description: string; task_type: string; trigger_type: string; cron_expression: string; is_enabled: number; config_json: string; last_run_at: string | null; next_run_at: string | null; created_at: string; updated_at: string }> }>('/scheduled-tasks')
  },

  /** 创建定时任务 */
  createScheduledTask(data: { name: string; description?: string; task_type?: string; trigger_type?: string; cron_expression?: string; is_enabled?: number; config_json?: string }) {
    return requestWithRetry<{ id: number; name: string; description: string; task_type: string; trigger_type: string; cron_expression: string; is_enabled: number; config_json: string; last_run_at: string | null; next_run_at: string | null; created_at: string; updated_at: string }>('/scheduled-tasks', { method: 'POST', body: JSON.stringify(data) })
  },

  /** 获取定时任务详情 */
  getScheduledTask(id: number) {
    return requestWithRetry<{ id: number; name: string; description: string; task_type: string; trigger_type: string; cron_expression: string; is_enabled: number; config_json: string; last_run_at: string | null; next_run_at: string | null; created_at: string; updated_at: string }>(`/scheduled-tasks/${id}`)
  },

  /** 更新定时任务 */
  updateScheduledTask(id: number, data: Partial<{ name: string; description: string; task_type: string; trigger_type: string; cron_expression: string; is_enabled: number; config_json: string }>) {
    return requestWithRetry<{ id: number; name: string; description: string; task_type: string; trigger_type: string; cron_expression: string; is_enabled: number; config_json: string; last_run_at: string | null; next_run_at: string | null; created_at: string; updated_at: string }>(`/scheduled-tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  /** 删除定时任务 */
  deleteScheduledTask(id: number) {
    return requestWithRetry<void>(`/scheduled-tasks/${id}`, { method: 'DELETE' })
  },

  /** 启用/禁用定时任务 */
  toggleScheduledTask(id: number) {
    return requestWithRetry<{ id: number; name: string; description: string; task_type: string; trigger_type: string; cron_expression: string; is_enabled: number; config_json: string; last_run_at: string | null; next_run_at: string | null; created_at: string; updated_at: string }>(`/scheduled-tasks/${id}/toggle`, { method: 'POST' })
  },

  /** 立即执行定时任务 */
  runScheduledTask(id: number) {
    return requestWithRetry<{ id: number; task_id: number; status: string; output: string; error: string; started_at: string; completed_at: string | null }>(`/scheduled-tasks/${id}/run`, { method: 'POST' })
  },

  /** 获取定时任务执行历史 */
  getScheduledTaskLogs(id: number, limit?: number) {
    const params = limit ? '?limit=' + limit : ''
    return requestWithRetry<{ logs: Array<{ id: number; task_id: number; status: string; output: string; error: string; started_at: string; completed_at: string | null }> }>(`/scheduled-tasks/${id}/logs` + params)
  },

  // ==================== 任务管理 API ====================

  /** 获取任务列表 */
  getTasks(params?: { status?: string; priority?: string; keyword?: string }) {
    const query = new URLSearchParams()
    if (params?.status) query.append('status', params.status)
    if (params?.priority) query.append('priority', params.priority)
    if (params?.keyword) query.append('keyword', params.keyword)
    const qs = query.toString()
    return requestWithRetry<{ items: Array<{ id: number; title: string; description: string; status: string; priority: string; assignee_id: string | null; assignee_name: string | null; reporter_id: string; reporter_name: string; project_id: number | null; tags: string[]; due_date: string | null; created_at: string; updated_at: string }>; total: number }>('/tasks' + (qs ? '?' + qs : ''))
  },

  /** 获取我的任务 */
  getMyTasks(status?: string) {
    const params = status ? '?status=' + status : ''
    return requestWithRetry<{ items: Array<{ id: number; title: string; description: string; status: string; priority: string; assignee_id: string | null; assignee_name: string | null; reporter_id: string; reporter_name: string; project_id: number | null; tags: string[]; due_date: string | null; created_at: string; updated_at: string }>; total: number }>('/tasks/my-tasks' + params)
  },

  /** 创建任务 */
  createTask(data: { title: string; description?: string; status?: string; priority?: string; assignee_id?: string | null; assignee_name?: string | null; project_id?: number | null; tags?: string[]; due_date?: string | null }) {
    return requestWithRetry<{ id: number; title: string; description: string; status: string; priority: string; assignee_id: string | null; assignee_name: string | null; reporter_id: string; reporter_name: string; project_id: number | null; tags: string[]; due_date: string | null; created_at: string; updated_at: string }>('/tasks', { method: 'POST', body: JSON.stringify(data) })
  },

  /** 更新任务 */
  updateTask(id: number, data: Partial<{ title: string; description: string; status: string; priority: string; assignee_id: string | null; assignee_name: string | null; project_id: number | null; tags: string[]; due_date: string | null }>) {
    return requestWithRetry<{ id: number; title: string; description: string; status: string; priority: string; assignee_id: string | null; assignee_name: string | null; reporter_id: string; reporter_name: string; project_id: number | null; tags: string[]; due_date: string | null; created_at: string; updated_at: string }>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  /** 更新任务状态 */
  updateTaskStatus(id: number, status: string) {
    return requestWithRetry<{ id: number; title: string; description: string; status: string; priority: string; assignee_id: string | null; assignee_name: string | null; reporter_id: string; reporter_name: string; project_id: number | null; tags: string[]; due_date: string | null; created_at: string; updated_at: string }>(`/tasks/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) })
  },

  /** 删除任务 */
  deleteTask(id: number) {
    return requestWithRetry<void>(`/tasks/${id}`, { method: 'DELETE' })
  },

  subscribeToEvents(role?: string, onEvent?: (data: any) => void): () => void {
    const params = role ? `?role=${role}` : ''
    let reconnectAttempts = 0
    const maxReconnectAttempts = 10
    let eventSource: EventSource | null = null
    let closed = false

    const connect = () => {
      if (closed) return
      eventSource = new EventSource(`/api/events/stream${params}`)

      eventSource.onmessage = (event) => {
        reconnectAttempts = 0
        try {
          const data = JSON.parse(event.data)
          onEvent?.(data)
        } catch {}
      }

      eventSource.onerror = () => {
        eventSource?.close()
        if (!closed && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts - 1), 30000)
          setTimeout(connect, delay)
        }
      }
    }

    connect()

    return () => {
      closed = true
      eventSource?.close()
    }
  },

  // ==================== 代码审查 API ====================

  /** 创建代码审查 */
  createCodeReview(data: {
    task_id: number
    diff: string
    project_context?: string
    model?: string
  }) {
    return requestWithRetry<{ id: number; task_id: number; status: string; created_at: string }>('/code-reviews', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /** 获取代码审查详情 */
  getCodeReview(reviewId: number) {
    return requestWithRetry<{ id: number; task_id: number; status: string; result: any; created_at: string; updated_at: string }>(`/code-reviews/${reviewId}`)
  },

  /** 获取代码审查列表 */
  listCodeReviews(params?: {
    task_id?: number
    project_id?: string
    status?: string
    limit?: number
    offset?: number
  }) {
    const query = new URLSearchParams()
    if (params?.task_id) query.append('task_id', String(params.task_id))
    if (params?.project_id) query.append('project_id', params.project_id)
    if (params?.status) query.append('status', params.status)
    if (params?.limit) query.append('limit', String(params.limit))
    if (params?.offset) query.append('offset', String(params.offset))
    const qs = query.toString()
    return requestWithRetry<Array<{ id: number; task_id: number; project_id: string; status: string; score: number | null; summary: string | null; created_at: string; updated_at: string }>>('/code-reviews' + (qs ? '?' + qs : ''))
  },

  /** 重新运行代码审查 */
  rerunCodeReview(reviewId: number) {
    return requestWithRetry<{ id: number; task_id: number; status: string; created_at: string; updated_at: string }>(`/code-reviews/${reviewId}/re-run`, {
      method: 'POST',
    })
  },
}
