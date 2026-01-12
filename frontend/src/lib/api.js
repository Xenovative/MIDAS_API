import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  console.log('API Request:', config.method?.toUpperCase(), config.url)
  console.log('Auth token present:', !!token)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.log('Token added to headers:', token.substring(0, 20) + '...')
  } else {
    console.warn('No auth token found in localStorage!')
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const conversationsApi = {
  list: () => api.get('/conversations/'),
  get: (id) => api.get(`/conversations/${id}`),
  create: (title) => api.post('/conversations/', { title }),
  delete: (id) => api.delete(`/conversations/${id}`),
  update: (id, title) => api.patch(`/conversations/${id}`, null, { params: { title } }),
}

export const chatApi = {
  send: (data) => api.post('/chat/', data),
  stream: (data) => {
    return fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
  },
}

export const modelsApi = {
  list: () => api.get('/models/'),
}

export const toolsApi = {
  list: () => api.get('/tools/'),
  execute: (toolName, parameters) => api.post(`/tools/${toolName}`, parameters),
}

export const configApi = {
  getApiKeys: () => api.get('/config/api-keys'),
  updateApiKeys: (keys) => api.post('/config/api-keys', keys),
  deleteApiKey: (provider) => api.delete(`/config/api-keys/${provider}`),
}

export const generationApi = {
  listImageModels: () => api.get('/generation/image/models'),
  generateImage: (data) => api.post('/generation/image', data),
  textToSpeech: (data) => api.post('/generation/tts', data, { responseType: 'blob' }),
  speechToText: (formData) => api.post('/generation/stt', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
}

export const suggestionsApi = {
  generate: (data) => api.post('/suggestions/generate', data),
}

export const botsApi = {
  list: () => api.get('/bots/'),
  get: (id) => api.get(`/bots/${id}`),
  create: (data) => api.post('/bots/', data),
  update: (id, data) => api.put(`/bots/${id}`, data),
  delete: (id) => api.delete(`/bots/${id}`),
}

export const documentsApi = {
  upload: (data) => api.post('/documents/upload', data),
  uploadFile: (file, botId = null, conversationId = null) => {
    const formData = new FormData()
    formData.append('file', file)
    const params = new URLSearchParams()
    if (botId) params.append('bot_id', botId)
    if (conversationId) params.append('conversation_id', conversationId)
    return api.post(`/documents/upload-file?${params.toString()}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  uploadFileWithProgress: async (file, botId = null, conversationId = null, onProgress) => {
    const params = new URLSearchParams()
    if (botId) params.append('bot_id', botId)
    if (conversationId) params.append('conversation_id', conversationId)
    
    const formData = new FormData()
    formData.append('file', file)
    
    // Get auth token from localStorage
    const token = localStorage.getItem('auth_token')
    const headers = {}
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    const response = await fetch(`${API_BASE_URL}/documents/upload-file-stream?${params.toString()}`, {
      method: 'POST',
      headers: headers,
      body: formData
    })
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (onProgress) onProgress(data)
          if (data.error) throw new Error(data.error)
          if (data.document) return data.document
        }
      }
    }
  },
  list: (botId) => api.get(`/documents/bot/${botId}`),
  delete: (documentId) => api.delete(`/documents/${documentId}`),
  search: (data) => api.post('/documents/search', data),
}

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getCurrentUser: () => api.get('/auth/me'),
  updateProfile: (data) => api.put('/auth/me', data),
  listUsers: () => api.get('/auth/users'),
  updateUser: (userId, data) => api.put(`/auth/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/auth/users/${userId}`),
}

export const adminApi = {
  getSettings: () => api.get('/admin/settings'),
  updateSetting: (key, data) => api.put(`/admin/settings/${key}`, data),
  getStats: () => api.get('/admin/stats'),
  listUsers: (skip = 0, limit = 50) => api.get('/admin/users', { params: { skip, limit } }),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (userId, data) => api.patch(`/admin/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  listModelPermissions: () => api.get('/admin/models/permissions'),
  getModelPermission: (modelId) => api.get(`/admin/models/permissions/${modelId}`),
  createModelPermission: (modelId, provider) => api.post(`/admin/models/permissions/${modelId}`, null, { params: { provider } }),
  updateModelPermission: (modelId, data) => api.patch(`/admin/models/permissions/${modelId}`, data),
  deleteModelPermission: (modelId) => api.delete(`/admin/models/permissions/${modelId}`),
  bulkCreatePermissions: () => api.post('/admin/models/permissions/bulk-create'),
}

export const mcpApi = {
  getStatus: () => api.get('/mcp/status'),
  listServers: () => api.get('/mcp/servers'),
  addServer: (data) => api.post('/mcp/servers', data),
  connectServer: (serverName) => api.post(`/mcp/servers/${serverName}/connect`),
  disconnectServer: (serverName) => api.post(`/mcp/servers/${serverName}/disconnect`),
  removeServer: (serverName) => api.delete(`/mcp/servers/${serverName}`),
  listTools: () => api.get('/mcp/tools'),
  callTool: (toolName, args) => api.post('/mcp/tools/call', { tool_name: toolName, arguments: args }),
  listResources: (serverName) => api.get(`/mcp/servers/${serverName}/resources`),
  readResource: (serverName, uri) => api.post(`/mcp/servers/${serverName}/resources/read`, null, { params: { uri } }),
}

export default api
