const API_BASE = ''

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<T>
}

export const api = {
  getHealth() {
    return request<{ status: string }>('/health')
  },

  getRequirements() {
    return request<Array<{ id: string; title: string; status: string }>>('/requirements/')
  },

  createRequirement(data: { requirement_raw_input: string }) {
    return request<{ id: string }>('/requirements/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  getApprovals(projectId: string) {
    return request<{ state: string; pending: boolean }>(`/approvals/${projectId}/state`)
  },

  submitApproval(projectId: string, status: 'approved' | 'rejected', comment?: string) {
    const params = new URLSearchParams({ status })
    if (comment) params.append('comment', comment)
    return request<{ success: boolean }>(`/approvals/${projectId}?${params.toString()}`, {
      method: 'POST',
    })
  },

  startWorkflow(projectId: string, data: { repo_path: string; raw_input: string }) {
    return request<{ workflow_id: string }>(`/workflow/${projectId}/start`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}
