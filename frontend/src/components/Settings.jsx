import { useState, useEffect } from 'react'
import { X, Thermometer, Zap, MessageSquare, Hash, FileText, Cpu, Database, Globe, Trash2, Key, CheckCircle, XCircle, AlertCircle, Eye, EyeOff, Save, RefreshCw, Wand2, Users, Shield } from 'lucide-react'
import { useStore } from '../store/useStore'
import { conversationsApi, configApi, modelsApi } from '../lib/api'
import ImageGenerator from './ImageGenerator'
import UserManagement from './UserManagement'
import ModelPermissions from './ModelPermissions'

export default function Settings({ isOpen, onClose }) {
  const { 
    temperature, 
    setTemperature, 
    useAgent, 
    setUseAgent,
    useRealtimeData,
    setUseRealtimeData,
    maxTokens,
    setMaxTokens,
    streamResponse,
    setStreamResponse,
    systemPrompt,
    setSystemPrompt,
    providers,
    setProviders,
    conversations,
    setConversations,
    setCurrentConversation,
    user
  } = useStore()
  
  const isAdmin = user?.role === 'admin'

  const [activeTab, setActiveTab] = useState('general')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [localMaxTokens, setLocalMaxTokens] = useState(maxTokens || '')
  const [showModelPermissions, setShowModelPermissions] = useState(false)
  
  // API Keys state
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    anthropic: '',
    google: '',
    openrouter: '',
    volcano: '',
    volcanoEndpoint: '',
    volcanoImageEndpoint: '',
    volcanoVideoEndpoint: '',
    deepseek: '',
    ollama: 'http://localhost:11434'
  })
  const [showKeys, setShowKeys] = useState({
    openai: false,
    anthropic: false,
    google: false,
    openrouter: false,
    volcano: false,
    deepseek: false
  })
  const [apiKeyStatus, setApiKeyStatus] = useState({})
  const [saving, setSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')
  const [refreshingModels, setRefreshingModels] = useState(false)
  const [expandedProvider, setExpandedProvider] = useState(null)
  const [enabledModels, setEnabledModels] = useState(() => {
    const saved = localStorage.getItem('enabledModels')
    return saved ? JSON.parse(saved) : {}
  })

  useEffect(() => {
    if (isOpen && activeTab === 'api') {
      loadApiKeyStatus()
    }
  }, [isOpen, activeTab])

  const loadApiKeyStatus = async () => {
    try {
      const response = await configApi.getApiKeys()
      setApiKeyStatus(response.data)
    } catch (error) {
      console.error('Failed to load API key status:', error)
    }
  }

  if (!isOpen) return null

  const handleClearAllConversations = async () => {
    try {
      for (const conv of conversations) {
        await conversationsApi.delete(conv.id)
      }
      setConversations([])
      setCurrentConversation(null)
      setShowDeleteConfirm(false)
    } catch (error) {
      console.error('Failed to clear conversations:', error)
    }
  }

  const handleMaxTokensChange = (value) => {
    setLocalMaxTokens(value)
    const num = parseInt(value)
    setMaxTokens(isNaN(num) || num <= 0 ? null : num)
  }

  const handleSaveApiKeys = async () => {
    setSaving(true)
    setSaveMessage('')
    try {
      const keysToUpdate = {}
      if (apiKeys.openai) keysToUpdate.openai_api_key = apiKeys.openai
      if (apiKeys.anthropic) keysToUpdate.anthropic_api_key = apiKeys.anthropic
      if (apiKeys.google) keysToUpdate.google_api_key = apiKeys.google
      if (apiKeys.openrouter) keysToUpdate.openrouter_api_key = apiKeys.openrouter
      if (apiKeys.volcano) keysToUpdate.volcano_api_key = apiKeys.volcano
      if (apiKeys.volcanoEndpoint) keysToUpdate.volcano_endpoint_id = apiKeys.volcanoEndpoint
      if (apiKeys.volcanoImageEndpoint) keysToUpdate.volcano_image_endpoint = apiKeys.volcanoImageEndpoint
      if (apiKeys.volcanoVideoEndpoint) keysToUpdate.volcano_video_endpoint = apiKeys.volcanoVideoEndpoint
      if (apiKeys.deepseek) keysToUpdate.deepseek_api_key = apiKeys.deepseek
      if (apiKeys.ollama) keysToUpdate.ollama_base_url = apiKeys.ollama

      const response = await configApi.updateApiKeys(keysToUpdate)
      setSaveMessage(response.data.message)
      
      // Clear input fields
      setApiKeys({
        openai: '',
        anthropic: '',
        google: '',
        openrouter: '',
        volcano: '',
        volcanoEndpoint: '',
        volcanoImageEndpoint: '',
        volcanoVideoEndpoint: '',
        deepseek: '',
        ollama: 'http://localhost:11434'
      })
      
      // Reload status
      await loadApiKeyStatus()
    } catch (error) {
      setSaveMessage('Error: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteApiKey = async (provider) => {
    try {
      await configApi.deleteApiKey(provider)
      await loadApiKeyStatus()
      setSaveMessage(`${provider} API key removed. Please restart backend.`)
    } catch (error) {
      setSaveMessage('Error: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleRefreshModels = async () => {
    setRefreshingModels(true)
    try {
      const response = await modelsApi.list()
      setProviders(response.data)
    } catch (error) {
      console.error('Failed to refresh models:', error)
      alert('Failed to refresh models: ' + error.message)
    } finally {
      setRefreshingModels(false)
    }
  }

  const toggleModelEnabled = (providerId, modelId) => {
    const key = `${providerId}:${modelId}`
    const newEnabledModels = {
      ...enabledModels,
      [key]: !enabledModels[key]
    }
    setEnabledModels(newEnabledModels)
    localStorage.setItem('enabledModels', JSON.stringify(newEnabledModels))
  }

  const isModelEnabled = (providerId, modelId) => {
    const key = `${providerId}:${modelId}`
    // Default to enabled if not set
    return enabledModels[key] !== false
  }

  const toggleAllModels = (providerId, enable) => {
    const provider = providers.find(p => p.provider === providerId)
    if (!provider) return
    
    const newEnabledModels = { ...enabledModels }
    provider.models.forEach(model => {
      const key = `${providerId}:${model.id}`
      newEnabledModels[key] = enable
    })
    setEnabledModels(newEnabledModels)
    localStorage.setItem('enabledModels', JSON.stringify(newEnabledModels))
  }

  const tabs = [
    { id: 'general', label: 'General', icon: MessageSquare },
    { id: 'model', label: 'Model', icon: Cpu },
    { id: 'generation', label: 'Image Generation', icon: Wand2 },
    ...(isAdmin ? [
      { id: 'users', label: 'Users', icon: Users },
      { id: 'api', label: 'API Keys', icon: Key },
      { id: 'advanced', label: 'Advanced', icon: FileText },
      { id: 'data', label: 'Data', icon: Database },
    ] : []),
    { id: 'about', label: 'About', icon: Globe },
  ]

  const renderContent = () => {
    switch (activeTab) {
      case 'general':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold mb-4">General Settings</h3>
            
            <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-accent transition-colors">
              <input
                type="checkbox"
                checked={streamResponse}
                onChange={(e) => setStreamResponse(e.target.checked)}
                className="w-4 h-4"
              />
              <div className="flex-1">
                <div className="font-medium text-sm">Stream Responses</div>
                <div className="text-xs text-muted-foreground">
                  Show AI responses in real-time as they're generated
                </div>
              </div>
            </label>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <Zap size={18} />
                <label className="font-medium">Agent Capabilities</label>
              </div>
              <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-accent transition-colors">
                <input
                  type="checkbox"
                  checked={useAgent}
                  onChange={(e) => setUseAgent(e.target.checked)}
                  className="w-4 h-4"
                />
                <div className="flex-1">
                  <div className="font-medium text-sm">Enable Agent Tools</div>
                  <div className="text-xs text-muted-foreground">
                    Allow AI to use web search, web scraping, calculator, and other tools
                  </div>
                </div>
              </label>
              <label className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-accent transition-colors mt-3">
                <input
                  type="checkbox"
                  checked={useRealtimeData}
                  onChange={(e) => setUseRealtimeData(e.target.checked)}
                  className="w-4 h-4"
                />
                <div className="flex-1">
                  <div className="font-medium text-sm">Use Realtime Web Context</div>
                  <div className="text-xs text-muted-foreground">
                    Auto-run web search to pull latest info before responding
                  </div>
                </div>
              </label>
            </div>
          </div>
        )

      case 'model':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold mb-4">Model Parameters</h3>
            
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Thermometer size={18} />
                <label className="font-medium">Temperature</label>
                <span className="ml-auto text-sm text-muted-foreground">{temperature.toFixed(1)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>Precise</span>
                <span>Balanced</span>
                <span>Creative</span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2">
                <Hash size={18} />
                <label className="font-medium">Max Tokens</label>
              </div>
              <input
                type="number"
                value={localMaxTokens}
                onChange={(e) => handleMaxTokensChange(e.target.value)}
                placeholder="Auto (model default)"
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                min="1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Maximum tokens to generate. Leave empty for model default.
              </p>
            </div>

            {isAdmin && (
              <div className="border-t border-border pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium">Available Providers</h4>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowModelPermissions(true)}
                      className="flex items-center gap-2 px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-accent transition-colors"
                    >
                      <Shield size={14} />
                      Model Permissions
                    </button>
                    <button
                      onClick={handleRefreshModels}
                      disabled={refreshingModels}
                      className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
                    >
                      <RefreshCw size={14} className={refreshingModels ? 'animate-spin' : ''} />
                      {refreshingModels ? 'Refreshing...' : 'Refresh Models'}
                    </button>
                  </div>
                </div>
              <div className="space-y-2">
                {providers.length > 0 ? (
                  providers.map((provider) => {
                    const isExpanded = expandedProvider === provider.provider
                    const enabledCount = provider.models.filter(m => isModelEnabled(provider.provider, m.id)).length
                    
                    return (
                      <div key={provider.provider} className="border border-border rounded-lg overflow-hidden">
                        <div className="p-3 bg-muted/30">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="font-medium capitalize">{provider.provider}</span>
                              <span className="text-xs bg-green-500/20 text-green-600 px-2 py-1 rounded">Active</span>
                            </div>
                            <button
                              onClick={() => setExpandedProvider(isExpanded ? null : provider.provider)}
                              className="text-xs px-3 py-1 bg-background border border-border rounded hover:bg-accent transition-colors"
                            >
                              {isExpanded ? 'Collapse' : 'Manage Models'}
                            </button>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {enabledCount} of {provider.models.length} model(s) enabled
                          </div>
                        </div>
                        
                        {isExpanded && (
                          <div className="p-3 border-t border-border">
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-sm font-medium">Available Models</span>
                              <div className="flex gap-2">
                                <button
                                  onClick={() => toggleAllModels(provider.provider, true)}
                                  className="text-xs px-2 py-1 bg-primary text-primary-foreground rounded hover:opacity-90"
                                >
                                  Enable All
                                </button>
                                <button
                                  onClick={() => toggleAllModels(provider.provider, false)}
                                  className="text-xs px-2 py-1 bg-muted rounded hover:bg-accent"
                                >
                                  Disable All
                                </button>
                              </div>
                            </div>
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                              {provider.models.map((model) => {
                                const enabled = isModelEnabled(provider.provider, model.id)
                                return (
                                  <label
                                    key={model.id}
                                    className="flex items-center gap-3 p-2 rounded hover:bg-accent cursor-pointer transition-colors"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={enabled}
                                      onChange={() => toggleModelEnabled(provider.provider, model.id)}
                                      className="w-4 h-4"
                                    />
                                    <div className="flex-1">
                                      <div className="text-sm font-medium flex items-center gap-2">
                                        {model.name}
                                        {model.supports_vision && (
                                          <span className="text-xs bg-purple-500/20 text-purple-600 px-1.5 py-0.5 rounded">
                                            Vision
                                          </span>
                                        )}
                                      </div>
                                      <div className="text-xs text-muted-foreground">
                                        {model.id} • {model.context_window.toLocaleString()} tokens
                                      </div>
                                    </div>
                                  </label>
                                )
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })
                ) : (
                  <div className="text-sm text-muted-foreground p-3 border border-border rounded-lg">
                    No providers configured. Add API keys in the API Keys tab.
                  </div>
                )}
              </div>
              </div>
            )}
          </div>
        )

      case 'generation':
        return <ImageGenerator />

      case 'users':
        return <UserManagement />

      case 'api':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-2">API Configuration</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Configure API keys directly. Changes require backend restart.
              </p>
            </div>

            {/* Save Message */}
            {saveMessage && (
              <div className={`p-3 rounded-lg text-sm ${saveMessage.includes('Error') ? 'bg-red-500/20 text-red-600' : 'bg-green-500/20 text-green-600'}`}>
                {saveMessage}
              </div>
            )}

            {/* API Key Inputs */}
            <div>
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Key size={18} />
                Configure API Keys
              </h4>
              <div className="space-y-4">
                {/* OpenAI */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-black dark:bg-white rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white dark:text-black font-bold text-sm">AI</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">OpenAI</div>
                      <div className="text-xs text-muted-foreground">
                        {apiKeyStatus.openai?.configured ? `Current: ${apiKeyStatus.openai.masked_key}` : 'Not configured'}
                      </div>
                    </div>
                    {apiKeyStatus.openai?.configured && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys.openai ? 'text' : 'password'}
                        value={apiKeys.openai}
                        onChange={(e) => setApiKeys({...apiKeys, openai: e.target.value})}
                        placeholder="sk-..."
                        className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                      <button
                        onClick={() => setShowKeys({...showKeys, openai: !showKeys.openai})}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                      >
                        {showKeys.openai ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Anthropic */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-sm">A</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">Anthropic</div>
                      <div className="text-xs text-muted-foreground">
                        {apiKeyStatus.anthropic?.configured ? `Current: ${apiKeyStatus.anthropic.masked_key}` : 'Not configured'}
                      </div>
                    </div>
                    {apiKeyStatus.anthropic?.configured && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys.anthropic ? 'text' : 'password'}
                        value={apiKeys.anthropic}
                        onChange={(e) => setApiKeys({...apiKeys, anthropic: e.target.value})}
                        placeholder="sk-ant-..."
                        className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                      <button
                        onClick={() => setShowKeys({...showKeys, anthropic: !showKeys.anthropic})}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                      >
                        {showKeys.anthropic ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Google */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-sm">G</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">Google AI</div>
                      <div className="text-xs text-muted-foreground">
                        {apiKeyStatus.google?.configured ? `Current: ${apiKeyStatus.google.masked_key}` : 'Not configured'}
                      </div>
                    </div>
                    {apiKeyStatus.google?.configured && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys.google ? 'text' : 'password'}
                        value={apiKeys.google}
                        onChange={(e) => setApiKeys({...apiKeys, google: e.target.value})}
                        placeholder="AI..."
                        className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                      <button
                        onClick={() => setShowKeys({...showKeys, google: !showKeys.google})}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                      >
                        {showKeys.google ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* OpenRouter */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-sm">OR</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">OpenRouter</div>
                      <div className="text-xs text-muted-foreground">
                        {apiKeyStatus.openrouter?.configured ? `Current: ${apiKeyStatus.openrouter.masked_key}` : 'Not configured'}
                      </div>
                    </div>
                    {apiKeyStatus.openrouter?.configured && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys.openrouter ? 'text' : 'password'}
                        value={apiKeys.openrouter}
                        onChange={(e) => setApiKeys({...apiKeys, openrouter: e.target.value})}
                        placeholder="sk-or-..."
                        className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                      <button
                        onClick={() => setShowKeys({...showKeys, openrouter: !showKeys.openrouter})}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                      >
                        {showKeys.openrouter ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Volcano Engine (火山引擎) */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-sm">火</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">火山引擎 (Volcano Engine)</div>
                      <div className="text-xs text-muted-foreground">
                        {apiKeyStatus.volcano?.configured ? `Current: ${apiKeyStatus.volcano.masked_key}` : 'Not configured'}
                      </div>
                    </div>
                    {apiKeyStatus.volcano?.configured && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <div className="flex-1 relative">
                        <input
                          type={showKeys.volcano ? 'text' : 'password'}
                          value={apiKeys.volcano}
                          onChange={(e) => setApiKeys({...apiKeys, volcano: e.target.value})}
                          placeholder="API Key"
                          className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                        />
                        <button
                          onClick={() => setShowKeys({...showKeys, volcano: !showKeys.volcano})}
                          className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                        >
                          {showKeys.volcano ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                    <input
                      type="text"
                      value={apiKeys.volcanoEndpoint}
                      onChange={(e) => setApiKeys({...apiKeys, volcanoEndpoint: e.target.value})}
                      placeholder="Chat Endpoint ID (e.g., ep-xxxxx)"
                      className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                    <input
                      type="text"
                      value={apiKeys.volcanoImageEndpoint}
                      onChange={(e) => setApiKeys({...apiKeys, volcanoImageEndpoint: e.target.value})}
                      placeholder="Image Endpoint ID (e.g., ep-xxxxx)"
                      className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                    <input
                      type="text"
                      value={apiKeys.volcanoVideoEndpoint}
                      onChange={(e) => setApiKeys({...apiKeys, volcanoVideoEndpoint: e.target.value})}
                      placeholder="Video Endpoint ID (e.g., ep-xxxxx)"
                      className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                    />
                  </div>
                </div>

                {/* DeepSeek */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-sm">DS</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">DeepSeek</div>
                      <div className="text-xs text-muted-foreground">
                        {apiKeyStatus.deepseek?.configured ? `Current: ${apiKeyStatus.deepseek.masked_key}` : 'Not configured'}
                      </div>
                    </div>
                    {apiKeyStatus.deepseek?.configured && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 relative">
                      <input
                        type={showKeys.deepseek ? 'text' : 'password'}
                        value={apiKeys.deepseek}
                        onChange={(e) => setApiKeys({...apiKeys, deepseek: e.target.value})}
                        placeholder="sk-..."
                        className="w-full px-3 py-2 pr-10 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                      />
                      <button
                        onClick={() => setShowKeys({...showKeys, deepseek: !showKeys.deepseek})}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-accent rounded"
                      >
                        {showKeys.deepseek ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Ollama */}
                <div className="p-4 border border-border rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-purple-500 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-sm">O</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium">Ollama (Local)</div>
                      <div className="text-xs text-muted-foreground">Base URL</div>
                    </div>
                    {providers.some(p => p.provider === 'ollama') && (
                      <CheckCircle size={18} className="text-green-600" />
                    )}
                  </div>
                  <input
                    type="text"
                    value={apiKeys.ollama}
                    onChange={(e) => setApiKeys({...apiKeys, ollama: e.target.value})}
                    placeholder="http://localhost:11434"
                    className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                  />
                </div>
              </div>

              {/* Save Button */}
              <button
                onClick={handleSaveApiKeys}
                disabled={saving}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                <Save size={18} />
                {saving ? 'Saving...' : 'Save API Keys'}
              </button>
            </div>

            {/* Quick Links */}
            <div className="border-t border-border pt-4">
              <h4 className="font-medium mb-3">Get API Keys</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <a 
                  href="https://platform.openai.com/api-keys" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
                >
                  OpenAI
                </a>
                <a 
                  href="https://console.anthropic.com/account/keys" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
                >
                  Anthropic
                </a>
                <a 
                  href="https://makersuite.google.com/app/apikey" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
                >
                  Google AI
                </a>
                <a 
                  href="https://openrouter.ai/keys" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
                >
                  OpenRouter
                </a>
                <a 
                  href="https://console.volcengine.com/ark" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
                >
                  火山引擎
                </a>
                <a 
                  href="https://ollama.ai/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-3 border border-border rounded-lg hover:bg-accent transition-colors text-center"
                >
                  Ollama
                </a>
              </div>
            </div>
          </div>
        )

      case 'advanced':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold mb-4">Advanced Settings</h3>
            
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FileText size={18} />
                <label className="font-medium">System Prompt</label>
              </div>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Enter a custom system prompt to guide the AI's behavior..."
                className="w-full px-3 py-2 border border-border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-ring min-h-[120px] resize-y"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Custom instructions prepended to every conversation. Leave empty for default.
              </p>
            </div>
          </div>
        )

      case 'data':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold mb-4">Data Management</h3>
            
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-2xl font-bold">{conversations.length}</div>
                  <div className="text-xs text-muted-foreground">Conversations</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">
                    {conversations.reduce((acc, conv) => acc + (conv.messages?.length || 0), 0)}
                  </div>
                  <div className="text-xs text-muted-foreground">Messages</div>
                </div>
              </div>
            </div>

            <div className="border border-red-500/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Trash2 size={18} className="text-red-500" />
                <h4 className="font-medium text-red-500">Danger Zone</h4>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Permanently delete all conversations. This cannot be undone.
              </p>
              {!showDeleteConfirm ? (
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
                >
                  Clear All Data
                </button>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Are you sure?</p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleClearAllConversations}
                      className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm"
                    >
                      Yes, Delete
                    </button>
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="px-4 py-2 border border-border rounded-lg hover:bg-accent text-sm"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )

      case 'about':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold mb-4">About MIDAS</h3>
            
            <div className="p-4 bg-muted/50 rounded-lg">
              <div className="text-sm font-medium mb-1">Version</div>
              <div className="text-2xl font-bold">1.0.0</div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Features</h4>
              <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                <li>Multi-LLM support (OpenAI, Anthropic, Google, OpenRouter, 火山引擎, Ollama)</li>
                <li>Real-time streaming responses</li>
                <li>Agent capabilities with web tools</li>
                <li>Conversation history management</li>
                <li>Customizable model parameters</li>
              </ul>
            </div>

            <div>
              <h4 className="font-medium mb-2">Tech Stack</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="p-2 bg-muted/50 rounded">
                  <div className="font-medium">Backend</div>
                  <div className="text-xs text-muted-foreground">FastAPI + Python</div>
                </div>
                <div className="p-2 bg-muted/50 rounded">
                  <div className="font-medium">Frontend</div>
                  <div className="text-xs text-muted-foreground">React + Vite</div>
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div 
        className="bg-background border border-border rounded-lg w-full max-w-3xl max-h-[85vh] overflow-hidden m-4 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-bold">Settings</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        
        {/* Guest/User Notice */}
        {user && (user.role === 'guest' || user.is_guest) && (
          <div className="mx-6 mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-yellow-600 dark:text-yellow-500">
              <AlertCircle size={16} />
              <span>
                <strong>Guest Mode:</strong> Some features are limited. Sign up for full access!
              </span>
            </div>
          </div>
        )}
        
        {user && user.role === 'free' && (
          <div className="mx-6 mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-500">
              <AlertCircle size={16} />
              <span>
                <strong>Free Plan:</strong> Upgrade to premium for unlimited messages and advanced features!
              </span>
            </div>
          </div>
        )}

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar Tabs */}
          <div className="w-48 border-r border-border p-2 overflow-y-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mb-1 ${
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-accent'
                  }`}
                >
                  <Icon size={16} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>

          {/* Content Area */}
          <div className="flex-1 p-6 overflow-y-auto">
            {renderContent()}
          </div>
        </div>
      </div>
      
      {/* Model Permissions Modal */}
      <ModelPermissions 
        isOpen={showModelPermissions}
        onClose={() => setShowModelPermissions(false)}
      />
    </div>
  )
}
