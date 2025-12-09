import axios from 'axios'
import type {
  ApiResponse,
  PaginatedResponse,
  ApiKey,
  CreateApiKeyRequest,
  UpdateApiKeyRequest,
  Workflow,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  Prompt,
  CreatePromptRequest,
  UpdatePromptRequest,
  ModelParameter,
  CreateModelParameterRequest,
  UpdateModelParameterRequest,
  LLMProvider,
  CreateLLMProviderRequest,
  UpdateLLMProviderRequest,
  SensitiveWordGroup,
  CreateSensitiveWordGroupRequest,
  UpdateSensitiveWordGroupRequest
} from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 1000000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    } else {
      // 如果没有 token，尝试从 workflow_ctl_api_key 读取（用于 ChatTestPage）
      const workflowApiKey = localStorage.getItem('workflow_ctl_api_key')
      if (workflowApiKey) {
        config.headers.Authorization = workflowApiKey.trim()
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// API Key 相关接口
export const apiKeyApi = {
  // 获取API Key列表
  getList: (params?: { page?: number; page_size?: number; search?: string }) =>
    api.get<PaginatedResponse<ApiKey>>('/apikeys/list', { params }),

  // 获取单个API Key
  getById: (id: string) =>
    api.get<ApiResponse<ApiKey>>('/apikeys/get', { params: { apikey_id: id } }),

  // 创建API Key
  create: (data: CreateApiKeyRequest) =>
    api.post<ApiResponse<ApiKey>>('/apikeys/create', data),

  // 更新API Key
  update: (id: string, data: UpdateApiKeyRequest) =>
    api.put<ApiResponse<ApiKey>>('/apikeys/update', data, { params: { apikey_id: id } }),

  // 删除API Key
  delete: (id: string) =>
    api.delete<ApiResponse<void>>('/apikeys/delete', { params: { apikey_id: id } }),

  // 获取统计信息
  getStats: () =>
    api.get<ApiResponse<{ total_count: number }>>('/apikeys/stats'),
}

// 流程配置相关接口
export const workflowApi = {
  // 获取流程列表
  getList: (params?: { page?: number; page_size?: number; search?: string; type?: string }) =>
    api.get<PaginatedResponse<Workflow>>('/workflows/list', { params }),

  // 获取单个流程
  getById: (id: string) =>
    api.get<ApiResponse<Workflow>>('/workflows/get', { params: { workflow_id: id } }),

  // 创建流程
  create: (data: CreateWorkflowRequest) =>
    api.post<ApiResponse<Workflow>>('/workflows/create', data),

  // 更新流程
  update: (id: string, data: UpdateWorkflowRequest) =>
    api.put<ApiResponse<Workflow>>('/workflows/update', data, { params: { workflow_id: id } }),

  // 删除流程
  delete: (id: string) =>
    api.delete<ApiResponse<void>>('/workflows/delete', { params: { workflow_id: id } }),

  // 获取统计信息
  getStats: () =>
    api.get<ApiResponse<{ total_count: number }>>('/workflows/stats'),
}

// Prompt 配置相关接口
export const promptApi = {
  // 获取Prompt列表
  getList: (params?: { page?: number; page_size?: number; search?: string; modelType?: string }) =>
    api.get<PaginatedResponse<Prompt>>('/prompts/list', { params }),

  // 获取单个Prompt
  getById: (id: string) =>
    api.get<ApiResponse<Prompt>>('/prompts/get', { params: { prompt_id: id } }),

  // 创建Prompt
  create: (data: CreatePromptRequest) =>
    api.post<ApiResponse<Prompt>>('/prompts/create', data),

  // 更新Prompt
  update: (id: string, data: UpdatePromptRequest) =>
    api.put<ApiResponse<Prompt>>('/prompts/update', data, { params: { prompt_id: id } }),

  // 删除Prompt
  delete: (id: string) =>
    api.delete<ApiResponse<void>>('/prompts/delete', { params: { prompt_id: id } }),

  // 获取统计信息
  getStats: () =>
    api.get<ApiResponse<{ total_count: number }>>('/prompts/stats'),
}

// 模型参数配置相关接口
export const modelParameterApi = {
  // 获取模型参数列表
  getList: (params?: { page?: number; page_size?: number; search?: string; modelType?: string }) =>
    api.get<PaginatedResponse<ModelParameter>>('/model-parameters/list', { params }),

  // 获取单个模型参数
  getById: (id: string) =>
    api.get<ApiResponse<ModelParameter>>('/model-parameters/get', { params: { parameter_id: id } }),

  // 创建模型参数
  create: (data: CreateModelParameterRequest) =>
    api.post<ApiResponse<ModelParameter>>('/model-parameters/create', data),

  // 更新模型参数
  update: (id: string, data: UpdateModelParameterRequest) =>
    api.put<ApiResponse<ModelParameter>>('/model-parameters/update', data, { params: { parameter_id: id } }),

  // 删除模型参数
  delete: (id: string) =>
    api.delete<ApiResponse<void>>('/model-parameters/delete', { params: { parameter_id: id } }),

  // 获取统计信息
  getStats: () =>
    api.get<ApiResponse<{ total_count: number }>>('/model-parameters/stats'),
}

// LLM Provider 配置相关接口
export const llmProviderApi = {
  // 获取LLM Provider列表
  getList: (params?: { page?: number; page_size?: number; search?: string; provider?: string }) =>
    api.get<PaginatedResponse<LLMProvider>>('/llm-providers/list', { params }),

  // 获取单个LLM Provider
  getById: (id: number) =>
    api.get<ApiResponse<LLMProvider>>('/llm-providers/get', { params: { provider_id: id } }),

  // 创建LLM Provider
  create: (data: CreateLLMProviderRequest) =>
    api.post<ApiResponse<LLMProvider>>('/llm-providers/create', data),

  // 更新LLM Provider
  update: (id: number, data: UpdateLLMProviderRequest) =>
    api.put<ApiResponse<LLMProvider>>('/llm-providers/update', data, { params: { provider_id: id } }),

  // 删除LLM Provider
  delete: (id: number) =>
    api.delete<ApiResponse<void>>('/llm-providers/delete', { params: { provider_id: id } }),
}

// 日志相关接口
export const logApi = {
  // 获取日志
  getLogs: (lines?: number) =>
    api.get<ApiResponse<{ content: string; line_count: number; lines: number }>>('/chat/logs', { params: { lines } }),

  // 获取日志统计（行数）
  getStats: () =>
    api.get<ApiResponse<{ content: string; line_count: number; lines: number }>>('/chat/logs', { params: { lines: 1 } }).then((res: any) => ({
      ...res,
      data: { total_count: res.data?.line_count || 0 }
    })) as Promise<ApiResponse<{ total_count: number }>>,

  // 获取最近7天的 token 消耗统计
  getTokenStats: () =>
    api.get<ApiResponse<any>>('/chat/stats'),
}

// 聊天日志相关接口
export const chatLogApi = {
  // 获取聊天日志列表
  getList: (params?: { skip?: number; limit?: number }) =>
    api.get('/chat-logs/', { params }) as Promise<{ total: number; items: any[] }>,
}

// 敏感词配置相关接口
export const sensitiveWordApi = {
  // 获取敏感词组列表
  getList: (params?: { page?: number; page_size?: number; search?: string }) =>
    api.get<PaginatedResponse<SensitiveWordGroup>>('/sensitive-words/list', { params }),

  // 获取单个敏感词组
  getById: (id: string) =>
    api.get<ApiResponse<SensitiveWordGroup>>('/sensitive-words/get', { params: { group_id: id } }),

  // 创建敏感词组
  create: (data: CreateSensitiveWordGroupRequest) =>
    api.post<ApiResponse<SensitiveWordGroup>>('/sensitive-words/create', data),

  // 更新敏感词组
  update: (id: string, data: UpdateSensitiveWordGroupRequest) =>
    api.put<ApiResponse<SensitiveWordGroup>>('/sensitive-words/update', data, { params: { group_id: id } }),

  // 删除敏感词组
  delete: (id: string) =>
    api.delete<ApiResponse<void>>('/sensitive-words/delete', { params: { group_id: id } }),

  // 获取统计信息
  getStats: () =>
    api.get<ApiResponse<{ total_count: number }>>('/sensitive-words/stats'),
}

export default api