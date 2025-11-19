import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
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

export default api
